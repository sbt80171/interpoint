import models
import views


def input_pt_on_edge(num: int) -> models.PtOnEdge:
    """
    入力ポイントデータの読み込み

    Parameters
    --------
    num : int
        データ番号（1 or 2）

    Returns
    --------
    ptonedge : models.PtOnEdge

    """
    fp = views.filepath_pt_on_edge(num)
    ptonedge = models.PtOnEdge(fp)
    views.geom_error(ptonedge)
    fld_m, fld_z = views.fieldname_mz(ptonedge.gdf)  # type: ignore
    for fld in [fld_m, fld_z]:
        views.dtype_error(ptonedge, fld)
    ptonedge.fieldname(fld_m, fld_z)
    return ptonedge


def main():
    views.intro()

    ptonedge1 = input_pt_on_edge(1)
    ptonedge2 = input_pt_on_edge(2)
    views.crs_error(ptonedge1, ptonedge2)

    pitch = views.pitch()
    i_div = views.i_div()
    fpout = views.filepath_out()

    ptonedge1.interpolate_lengthwide(pitch)
    ptonedge2.interpolate_lengthwide(pitch)
    views.m_error(ptonedge1, ptonedge2)

    ptall = models.PtAll(ptonedge1.gdf.crs)
    ptall.interpolate_crosswide(ptonedge1, ptonedge2, i_div)
    ptall.output_shp(fpout)
