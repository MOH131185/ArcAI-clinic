import os
import shutil
import ezdxf
import ifcopenshell
from pathlib import Path

def dxf_to_ifc(dxf_path: str) -> str:
    ifc_path = str(Path(dxf_path).with_suffix(".ifc"))
    shutil.copy(dxf_path, ifc_path)
    return ifc_path
# Path where your LoRA-styled DXFs live; outputs must already exist
# (i.e. styled PNG → styled DXF happens in ring2 or ring3)
def dxf_to_ifc(dxf_path: str) -> str:
    """
    Read a DXF from outputs/, turn it into a trivial IFC building.
    Returns the path to the new .ifc file in outputs/.
    """
    if not os.path.isfile(dxf_path):
        raise FileNotFoundError(f"DXF not found at {dxf_path}")

    # Ensure outputs folder still exists
    os.makedirs("outputs", exist_ok=True)

    # Load the DXF
    doc = ezdxf.readfile(dxf_path)
    modelspace = doc.modelspace()

    # Create a new IFC project
    project = ifcopenshell.api.run(
        "root.create_entity",
        ifcopenshell.file(),
        ifc_class="IfcProject"
    )
    # Simple site, building, storey
    site     = ifcopenshell.api.run("root.create_entity", project, ifc_class="IfcSite")
    building = ifcopenshell.api.run("root.create_entity", project, ifc_class="IfcBuilding")
    storey  = ifcopenshell.api.run("root.create_entity", project, ifc_class="IfcBuildingStorey")

    # Aggregate hierarchy
    ifcopenshell.api.run("aggregate.assign_object", project, related_object=site)
    ifcopenshell.api.run("aggregate.assign_object", site,    related_object=building)
    ifcopenshell.api.run("aggregate.assign_object", building, related_object=storey)

    # For each LWPolyline in the DXF, create an IfcPolyline
    for e in modelspace.query("LWPOLYLINE"):
        points = [(p[0], p[1], 0.0) for p in e.get_points()]
        ifc_poly = ifcopenshell.api.run(
            "geometry.add_polyline",
            project,
            points=points
        )
        # Place it under the storey
        ifcopenshell.api.run(
            "aggregate.assign_object",
            storey,
            relating_object=ifc_poly
        )

    # Save out the IFC
    ifc_filename = os.path.splitext(os.path.basename(dxf_path))[0] + ".ifc"
    ifc_path = os.path.join("outputs", ifc_filename)
    project.write(ifc_path)

    return ifc_path
# backend/ring4/ifc_exporter.py

def convert_dxf_to_ifc(dxf_path: str, ifc_path: str) -> str:
    """
    Stub: simply copies the DXF to a .ifc file.
    Replace with IfcOpenShell logic.
    """
    with open(dxf_path, "rb") as src, open(ifc_path, "wb") as dst:
        dst.write(src.read())
    return ifc_path
