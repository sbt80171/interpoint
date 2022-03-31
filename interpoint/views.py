import os.path

import geopandas as gpd

import models


def intro() -> None:
    print('ポイントデータの座標と値（標高値など）をもとに線形補間')
    print()


def filepath_pt_on_edge(num: int) -> str:
    print(f'{num}つめの入力ファイルを指定')
    fp = input('>> ')
    print()
    return fp


def fieldname_mz(gdf: gpd.GeoDataFrame) -> tuple[str, str]:
    print('No  Field      Type')
    print('------------------------')
    for i, dtype_column in enumerate(zip(gdf.dtypes, gdf.dtypes.index)):
        dtype, column = dtype_column
        if column != 'geometry':
            print(f'{i: 0}  {column: <10}  {dtype}')

    print()
    print('縦断距離を格納したフィールドの番号を指定')
    num_m = int(input('>> '))
    print('標高値を格納したフィールドの番号を指定')
    num_z = int(input('>> '))

    columns = gdf.columns.tolist()
    fieldname_m = columns[num_m]
    fieldname_z = columns[num_z]
    print()

    return fieldname_m, fieldname_z


def pitch() -> float:
    print('縦断方向の分割間隔を指定')
    pitch = float(input('>> '))
    return pitch


def i_div() -> int:
    print('横断方向の分割数を指定')
    i_div = int(input('>> '))
    return i_div


def filepath_out() -> str:
    print('出力フォルダを指定')
    fold = input('>> ')
    print('出力ファイル名を指定（拡張子不要）')
    fn = input('>> ')
    fp = os.path.join(fold, fn + '.shp')
    return fp


def geom_error(ptonedge: models.PtOnEdge) -> None:
    if not ptonedge.is_point():
        raise TypeError('ポイントタイプのデータを指定して下さい')
    else:
        return None


def dtype_error(ptonedge: models.PtOnEdge, fld: str) -> None:
    if not ptonedge.is_numeric(fld):
        raise TypeError(f'数値型のフィールドを指定して下さい {fld}')
    else:
        return None


def crs_error(
    ptonedge1: models.PtOnEdge,
    ptonedge2: models.PtOnEdge
) -> None:
    if not models.is_equal_projected_crs(ptonedge1, ptonedge2):
        raise TypeError('同一の投影座標系のデータを指定して下さい')
    else:
        return None


def m_error(
    ptonedge1: models.PtOnEdge,
    ptonedge2: models.PtOnEdge
) -> None:
    if not models.is_equal_m(ptonedge1, ptonedge2):
        raise TypeError('縦断距離の設定が等しいデータを指定して下さい')
    else:
        return None
