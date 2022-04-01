import glob
import os
import sys

import geopandas as gpd
import pandas as pd
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from interpoint import models


COLS_MZXY = ['kyori', 'z', 'x', 'y']
COLS_MZ = ['kyori', 'z']
CRS = 'EPSG:2449'

TBL1 = [
    [0, 10.0, 0.0, 0.0],
    [100, 11.0, 100.0, 100.0],
    [200, 12.0, 200.0, 200.0],
    [300, 13.0, 300.0, 300.0],
    [400, 14.0, 400.0, 400.0]
    ]
TBL2 = [
    [0, 10.0, 0.0, 100.0],
    [100, 11.0, 100.0, 200.0],
    [200, 12.0, 200.0, 300.0],
    [300, 13.0, 300.0, 400.0],
    [400, 14.0, 400.0, 500.0]
    ]
TMPFOLD = os.path.join(os.path.dirname(__file__), 'tmp')


def tbl2gdf(tbl: list, colx='x', coly='y', crs=CRS) -> gpd.GeoDataFrame:
    """ 前処理用
    pt の GeoDataFrame を返す
    """
    df = pd.DataFrame(tbl, columns=COLS_MZXY)
    gdf = gpd.GeoDataFrame(
        df[COLS_MZ],
        crs=crs,
        geometry=gpd.points_from_xy(df[colx], df[coly]))
    return gdf


def delfiles(fn: str) -> None:
    """ 後処理用
    シェープファイル を削除
    """
    files = glob.glob(os.path.join(TMPFOLD, os.path.splitext(fn)[0] + '.*'))
    for fp in files:
        os.remove(fp)


@pytest.fixture
def fp_pt1(fn='pt1.shp'):
    fp = os.path.join(TMPFOLD, fn)
    gdf = tbl2gdf(TBL1)
    gdf.to_file(fp)
    yield fp
    delfiles(fn)


@pytest.fixture
def fp_pt2(fn='pt2.shp'):
    fp = os.path.join(TMPFOLD, fn)
    gdf = tbl2gdf(TBL2)
    gdf.to_file(fp)
    yield fp
    delfiles(fn)


@pytest.fixture
def ptall(fp_pt1, fp_pt2, fn='ptall.shp'):
    ptonedge1 = models.PtOnEdge(fp_pt1)
    ptonedge2 = models.PtOnEdge(fp_pt2)
    ptonedge1.fieldname(*COLS_MZ)
    ptonedge2.fieldname(*COLS_MZ)
    ptonedge1.interpolate_lengthwide(pitch=10.0)
    ptonedge2.interpolate_lengthwide(pitch=10.0)
    ptall = models.PtAll(CRS)
    ptall.interpolate_crosswide(ptonedge1, ptonedge2, 10)
    yield ptall
