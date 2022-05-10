"""
縦横断方向に値を線形補間
入力ポイント間は直線
"""
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import interpolate


class PtOnEdge:
    def __init__(self, fp: str) -> None:
        """
        横断ラインの始点または終点を縦断方向に並べたポイントデータ

        Parameters
        --------
        fp : str
            ポイントデータのファイルパス

        Attributes
        --------
        gdf : gpd.GeoDataFrame
            ポイントデータ
        """
        # 'm', 'z', 'x', 'y', 'geometry'
        self.gdf = gpd.read_file(fp)
        self.crs = self.gdf.crs

    def is_point(self) -> bool:
        """
        ジオメトリがポイントであることの判定
        """
        return self.gdf.loc[0, 'geometry'].geom_type == 'Point'

    def is_numeric(self, fld) -> None:
        """
        フィールドが数値型であることの判定
        """
        return self.gdf[fld].dtype != 'object'  # type: ignore

    def fieldname(self, fld_m: str, fld_z: str) -> None:
        """
        縦断距離と値のフィールドを取得
        'geometry'は残して、それ以外のフィールドを削除
        縦断距離で昇順ソート

        Parameters
        --------
        fld_m : str
            縦断距離を格納したフィールドの名前
        fld_z : str
            値を格納したフィールドの名前
        """
        self.gdf = self.gdf[[fld_m, fld_z, 'geometry']]
        self.gdf = self.gdf.sort_values(fld_m)
        self.gdf = self.gdf.rename(
            columns={fld_m: 'm', fld_z: 'z'})  # type: ignore

    def interpolate_lengthwide(self, pitch: float) -> None:
        """
        指定の縦断距離ピッチで値を線形補間

        Parameters
        --------
        pitch : float
            縦断距離ピッチ
        """
        # 縦断距離を細分化
        mmin = self.gdf['m'].min()
        mmax = self.gdf['m'].max()
        div_m = np.arange(mmin, mmax, pitch)
        div_m = np.append(div_m, mmax)
        df = pd.DataFrame([div_m]).transpose()
        df.columns = ['m']
        df = df.merge(self.gdf, on='m', how='outer')
        df = df.sort_values('m')

        # xy座標を取得
        df[['x', 'y']] = df[~df['geometry'].isnull()].apply(
            lambda row: row['geometry'].coords[0],
            axis=1,
            result_type='expand')

        # xyz座標をそれぞれ線形補間
        df_tmp = df[~df['geometry'].isnull()]
        f_z = interpolate.interp1d(df_tmp['m'], df_tmp['z'])
        f_x = interpolate.interp1d(df_tmp['m'], df_tmp['x'])
        f_y = interpolate.interp1d(df_tmp['m'], df_tmp['y'])
        div_z = f_z(div_m)
        div_x = f_x(div_m)
        div_y = f_y(div_m)

        # gpd.GeoDataFrame を再構成
        df = pd.DataFrame([div_m, div_z, div_x, div_y]).transpose()
        df.columns = ['m', 'z', 'x', 'y']
        self.gdf = gpd.GeoDataFrame(
            df,
            crs=self.crs,
            geometry=gpd.points_from_xy(df['x'], df['y'], df['z']))


class PtAll:
    def __init__(self, crs) -> None:
        """
        線形補間ポイントデータ
        """
        # 'i', 'x', 'y', 'm', 'z', 'geometry'
        self.gdf: gpd.GeoDataFrame
        self.crs = crs

    def interpolate_crosswide(
        self, pt1: PtOnEdge, pt2: PtOnEdge, i_div: int
    ) -> None:
        """
        横断方向に線形補間

        Parameters
        --------
        pt1 : PtOnEdge
            一方のポイントデータ
        pt2 : PtOnEdge
            他方のポイントデータ
        i_div : int
            横断方向の分割数
        """
        def div_xyz(col: str) -> pd.DataFrame:
            """
            両端の間の座標と値を線形補間

            Parameters
            --------
            col : str
                'x' or 'y' or 'z'

            Returns
            --------
            df : pd.DataFrame
                カラム名は左から連番
                左端のカラムに pt1 の座標、右側のカラムに pt2 の座標
                縦は縦断方向、横に横断方向
            """
            df1 = pt1.gdf[[col]].rename(columns={col: 0})  # type: ignore
            df2 = pt2.gdf[[col]].rename(columns={col: i_div})  # type: ignore

            warnings.simplefilter('ignore')

            for i in range(1, i_div):
                df1[i] = np.nan

            warnings.resetwarnings()

            df = pd.concat([df1, df2], axis=1)
            df = df.interpolate(axis=1)
            return df
        # カラム別に線形補間
        dfx = div_xyz('x').melt(var_name='i', value_name='x')
        dfy = div_xyz('y').melt(var_name='i', value_name='y')
        dfm = div_xyz('m').melt(var_name='i', value_name='m')
        dfz = div_xyz('z').melt(var_name='i', value_name='z')

        # gpd.GeoDataFrame を再構成
        df = pd.concat([dfx, dfy, dfm, dfz], axis=1)
        df = df.loc[:, ~df.columns.duplicated()]  # i列重複削除
        self.gdf = gpd.GeoDataFrame(
            df,
            crs=self.crs,
            geometry=gpd.points_from_xy(df['x'], df['y'], df['z']))

    def output_shp(self, fp: str):
        """
        シェープファイルに出力

        Parameters
        --------
        fp : str
        出力ファイルパス
        """
        self.gdf[['i', 'm', 'z', 'geometry']].to_file(fp, encoding='utf-8')


def is_equal_projected_crs(pt1: PtOnEdge, pt2: PtOnEdge) -> bool:
    """
    2つの PtOnEdge オブジェクトにおいて crs の同一性を確認する

    Parameters
    --------
    pt1 : PtOnEdge
        一方のポイントデータ
    pt2 : PtOnEdge
        他方のポイントデータ

    Returns
    --------
    bool
        同一の投影座標系の場合は True、それ以外の場合は False
    """
    crs1 = pt1.gdf.crs
    crs2 = pt2.gdf.crs
    if (crs1 is None) or (crs2 is None):
        # 定義がない
        return False
    elif not (crs1.is_projected and crs2.is_projected):  # type: ignore
        # 投影座標ではない
        return False
    elif crs1 != crs2:
        # 座標系が同一ではない
        return False
    else:
        return True


def is_equal_m(pt1: PtOnEdge, pt2: PtOnEdge) -> bool:
    """
    2つの PtOnEdge オブジェクトの m の一致を確認する

    Parameters
    --------
    pt1 : PtOnEdge
        一方のポイントデータ
    pt2 : PtOnEdge
        他方のポイントデータ

    Returns
    --------
    bool
        同一の場合は True、同一でない場合は False
    """
    if pt1.gdf['m'].to_list() != pt2.gdf['m'].to_list():  # type: ignore
        return False
    else:
        return True


if __name__ == '__main__':
    pass
