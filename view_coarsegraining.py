import numpy as np
import holoviews as hv
import panel as pn
import argparse
import xarray as xr
from linear_regression import LinearRegression_xr

from os.path import join


def parse_args():
    parser = argparse.ArgumentParser(
        description="Coarse-graining of active particle simulation data"
    )
    parser.add_argument(
        "sim_folder_path", help="Path to folder containing simulation data", type=str
    )
    return parser.parse_args()


def main():
    parms = parse_args()
    sim_path = parms.sim_folder_path
    cg_ds = xr.open_dataset(join(sim_path, "cg_data.nc"))
    asp = cg_ds.attrs["L"] / cg_ds.attrs["l"]
    cg_ds = cg_ds.assign(
        px=(cg_ds.psi.dims, (cg_ds.psi * cg_ds.rho * cg_ds.px).data, cg_ds.px.attrs),
        py=(cg_ds.psi.dims, (cg_ds.psi * cg_ds.rho * cg_ds.py).data, cg_ds.py.attrs),
    )

    cg_ds = cg_ds.assign(
        grad_rhox=lambda arr: (
            ["t", "theta", "y", "x"],
            (arr.psi * (arr.rho.roll(x=-1) - arr.rho.roll(x=1))).data,
            {"name": "density_gradient", "average": 1, "type": "vector", "dir": "x"},
        )
    )
    cg_ds = cg_ds.assign(
        grad_rhoy=lambda arr: (
            ["t", "theta", "y", "x"],
            (arr.psi * (arr.rho.roll(y=-1) - arr.rho.roll(y=1))).data,
            {"name": "density_gradient", "average": 1, "type": "vector", "dir": "y"},
        )
    )

    cg_ds = cg_ds.assign(
        ex=(
            ["t", "theta", "y", "x"],
            (cg_ds.psi * (cg_ds.rho * np.cos(cg_ds.theta))).data,
            {"name": "e", "average": 0, "type": "vector", "dir": "x"},
        ),
        ey=(
            ["t", "theta", "y", "x"],
            (cg_ds.psi * (cg_ds.rho * np.sin(cg_ds.theta))).data,
            {"name": "e", "average": 0, "type": "vector", "dir": "y"},
        ),
    )

    cg_ds.assign(Fx=cg_ds.Fx / cg_ds.psi, Fy=cg_ds.Fy / cg_ds.psi)

    # Linear regression fit of the forces with fields (grad_rho, p)
    lr = LinearRegression_xr(
        target_field="force", training_fields=["density_gradient", "polarity", "e"]
    )
    lr.fit(cg_ds)
    cg_ds = lr.predict_on_dataset(cg_ds)

    def split_by_attr(ds, attr_name):
        fields = {}
        for var_name, variable in ds.items():
            attr_value = variable.attrs.get(attr_name)
            if not attr_value:
                raise (
                    ValueError(
                        f"Variable {var_name} doesn't have attribute {attr_name}"
                    )
                )
            if not attr_value in fields.keys():
                fields[attr_value] = [variable]
            else:
                fields[attr_value].append(variable)
        return fields

    def list_fields(ds: xr.Dataset, **kwargs):
        list_fields = []
        for field in ds.filter_by_attrs(**kwargs):
            field_name = ds[field].attrs["name"]
            if field_name in list_fields:
                continue
            list_fields.append(field_name)
        return list_fields

    dic_vector_widgets = {}
    dims = dict(cg_ds.sizes)

    for vector_field in list_fields(cg_ds, type="vector"):
        x_data = (
            cg_ds.filter_by_attrs(type="vector", dir="x", name=vector_field)
            .to_dataarray()
            .broadcast_like(cg_ds)
            .squeeze(dim="variable", drop=True)
            .data
        )
        y_data = (
            cg_ds.filter_by_attrs(type="vector", dir="y", name=vector_field)
            .to_dataarray()
            .broadcast_like(cg_ds)
            .squeeze(dim="variable", drop=True)
            .data
        )
        cg_ds[f"{vector_field}_mag"] = (
            list(dims.keys()),
            np.sqrt(x_data**2 + y_data**2),
        )
        cg_ds[f"{vector_field}_angle"] = (
            list(dims.keys()),
            np.arctan2(y_data, x_data),
        )
        dic_vector_widgets[f"{vector_field}_checkbox"] = pn.widgets.Checkbox(
            name=vector_field
        )
        dic_vector_widgets[f"{vector_field}_color"] = pn.widgets.ColorPicker(
            name=f"{vector_field} color", value="red"
        )

    list_t = list(cg_ds.t.data)
    t_slider = pn.widgets.DiscreteSlider(name="t", options=list_t)
    list_th = list(cg_ds.theta.data)
    th_slider = pn.widgets.DiscreteSlider(name="theta", options=list_th)
    select_color_field = pn.widgets.Select(
        name="Color by field", value="psi", options=["psi", "rho"]
    )
    select_cmap = pn.widgets.Select(
        name="Color Map", value="blues", options=["blues", "jet", "Reds"]
    )

    def plot_data(t, th, col_field, cmap, **widgets):
        data = cg_ds.sel(t=t, theta=th)
        plot = hv.HeatMap((data["x"], data["y"], data[col_field])).opts(
            cmap=cmap,
            clim=(float(cg_ds[col_field].min()), float(cg_ds[col_field].max())),
            width=400,
            height=int(asp * 400),
        )
        for vector_field in list_fields(cg_ds, type="vector"):
            plot = plot * hv.VectorField(
                (
                    data["x"],
                    data["y"],
                    data[f"{vector_field}_angle"],
                    data[f"{vector_field}_mag"],
                )
            ).opts(
                alpha=1.0 if widgets[f"{vector_field}_checkbox"] else 0,
                color=widgets[f"{vector_field}_color"],
            ).opts(
                magnitude=hv.dim("Magnitude").norm()
            )
        return plot

    dmap = hv.DynamicMap(
        pn.bind(
            plot_data,
            t=t_slider,
            th=th_slider,
            col_field=select_color_field,
            cmap=select_cmap,
            **dic_vector_widgets,
        )
    )

    row = pn.Row(
        pn.WidgetBox(
            pn.Column(
                t_slider,
                th_slider,
                select_color_field,
                select_cmap,
                *[
                    pn.Row(
                        dic_vector_widgets[f"{field}_checkbox"],
                        dic_vector_widgets[f"{field}_color"],
                    )
                    for field in list_fields(cg_ds, type="vector")
                ],
            )
        ),
        dmap,
    )
    return cg_ds, row, lr


if __name__ == "__main__":
    import sys
    from unittest.mock import patch

    pn.extension()
    sim_path = (
        r"C:\Users\nolan\Documents\PhD\Simulations\Data\Compute_forces\Batch\_temp"
    )
    args = ["prog", sim_path]
    with patch.object(sys, "argv", args):
        cg_ds, row, lr = main()
        row
