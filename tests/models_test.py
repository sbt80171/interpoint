import os.path
import sys

import pytest
from shapely.geometry import LineString
from shapely.geometry import Point

import conftest

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from interpoint import models


class TestPtOnEdge:
    def test_is_point(self, fp_pt1):
        """
        Point と LineString をテスト
        """
        ptonedge = models.PtOnEdge(fp_pt1)
        assert ptonedge.is_point()
        ptonedge.gdf['geometry'] = LineString([(0, 0), (1, 1)])
        assert not ptonedge.is_point()

    def test_is_numeric_m(self, fp_pt1):
        """
        縦断距離フィールドで、数値と文字列をテスト
        """
        ptonedge = models.PtOnEdge(fp_pt1)
        fld_m = ptonedge.gdf.columns[0]
        assert ptonedge.is_numeric(fld_m)
        ptonedge.gdf[fld_m] = [c for c in 'abcde']
        assert not ptonedge.is_numeric(fld_m)

    def test_is_numeric_z(self, fp_pt1):
        """
        標高値フィールドで、数値と文字列をテスト
        """
        ptonedge = models.PtOnEdge(fp_pt1)
        fld_z = ptonedge.gdf.columns[1]
        assert ptonedge.is_numeric(fld_z)
        ptonedge.gdf[fld_z] = [c for c in 'abcde']
        assert not ptonedge.is_numeric(fld_z)

    def test_fieldname(self, fp_pt1):
        """
        カラム名と縦断距離昇順をテスト
        """
        ptonedge = models.PtOnEdge(fp_pt1)
        ptonedge.fieldname(*conftest.COLS_MZ)
        list_columns = ptonedge.gdf.columns.tolist()
        assert list_columns == ['m', 'z', 'geometry']
        assert ptonedge.gdf['m'].is_monotonic  # type: ignore

    @pytest.mark.parametrize(('idx', 'm', 'z', 'x', 'y'), [
        (0, 0, 10, 0, 0),
        (15, 150, 11.5, 150, 150),
        (40, 400, 14, 400, 400)
    ])
    def test_interpolate_lengthwide(self, fp_pt1, idx, m, z, x, y):
        """
        NAテストと、同値テスト
        """
        pitch = 10.0
        ptonedge = models.PtOnEdge(fp_pt1)
        ptonedge.fieldname(*conftest.COLS_MZ)
        ptonedge.interpolate_lengthwide(pitch=pitch)
        assert ptonedge.gdf.isnull().values.sum() == 0  # type: ignore
        list_mzxyg = ptonedge.gdf.iloc[idx].tolist()  # type: ignore
        assert list_mzxyg == [m, z, x, y, Point(x, y, z)]


class TestPtAll:
    @pytest.mark.parametrize(('idx', 'i', 'x', 'y', 'm', 'z'), [
        (0, 0, 0.0, 0.0, 0.0, 10.0),
        (100, 2, 180.0, 200.0, 180.0, 11.8),
        (450, 10, 400.0, 500.0, 400.0, 14.0)
    ])
    def test_interpolate_crosswide(
        self, ptall: models.PtAll, idx, i, x, y, m, z
    ):
        """
        NAテストと、同値テスト
        """
        assert ptall.gdf.isnull().values.sum() == 0
        list_ixymzg = ptall.gdf.iloc[idx].tolist()  # type: ignore
        assert list_ixymzg == [i, x, y, m, z, Point(x, y, z)]

    def test_output_shp(self, ptall: models.PtAll, fn='ptall.shp'):
        """
        シェープファイル出力テスト
        """
        fp = os.path.join(conftest.TMPFOLD, fn)
        ptall.output_shp(fp)
        assert os.path.isfile(fp)
        conftest.delfiles(fn)


def test_is_qual_projected_crs(fp_pt1, fp_pt2):
    """
    crs投影座標一致、定義なし、地理座標、不一致をテスト
    """
    ptonedge1 = models.PtOnEdge(fp_pt1)
    ptonedge2 = models.PtOnEdge(fp_pt2)
    assert models.is_equal_projected_crs(ptonedge1, ptonedge2)
    ptonedge1.gdf.crs = None
    assert not models.is_equal_projected_crs(ptonedge1, ptonedge2)
    ptonedge1.gdf.crs = 'EPSG:4612'
    assert not models.is_equal_projected_crs(ptonedge1, ptonedge2)
    ptonedge1.gdf.crs = 'EPSG:2443'
    ptonedge2.gdf.crs = 'EPSG:2444'
    assert not models.is_equal_projected_crs(ptonedge1, ptonedge2)


def test_is_equal_m(fp_pt1, fp_pt2):
    """
    2つの PtOnEdge の縦断距離で、一致と不一致をテスト
    """
    ptonedge1 = models.PtOnEdge(fp_pt1)
    ptonedge2 = models.PtOnEdge(fp_pt2)
    ptonedge1.fieldname(*conftest.COLS_MZ)
    ptonedge2.fieldname(*conftest.COLS_MZ)
    assert models.is_equal_m(ptonedge1, ptonedge2)
    ptonedge1.gdf['m'] = ptonedge1.gdf['m'] + 1  # type: ignore
    assert not models.is_equal_m(ptonedge1, ptonedge2)
