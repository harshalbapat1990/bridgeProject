from enum import Enum

class SpeckleTypes(str, Enum):
    # Data Entities
    COLLECTION = "Speckle.Core.Models.Collections.Collection"
    DATA_OBJECT = "Objects.Data.DataObject"
    
    # Geometry Entities
    GEOMETRY_ARC = "Objects.Geometry.Arc"
    GEOMETRY_LINE = "Objects.Geometry.Line"
    GEOMETRY_MESH = "Objects.Geometry.Mesh"
    GEOMETRY_PLANE = "Objects.Geometry.Plane"
    GEOMETRY_POINT = "Objects.Geometry.Point"
    GEOMETRY_POLYLINE = "Objects.Geometry.Polyline"
    GEOMETRY_REGION = "Objects.Geometry.Region"
    GEOMETRY_VECTOR = "Objects.Geometry.Vector"
    GEOMETRY_BOX = "Objects.Geometry.Box"
    GEOMETRY_CIRCLE = "Objects.Geometry.Circle"
    GEOMETRY_CONTROL_POINT = "Objects.Geometry.ControlPoint"
    GEOMETRY_ELLIPSE = "Objects.Geometry.Ellipse"
    GEOMETRY_POINT_CLOUD = "Objects.Geometry.PointCloud"
    GEOMETRY_POLYCURVE = "Objects.Geometry.Polycurve"
    GEOMETRY_SPIRAL = "Objects.Geometry.Spiral"
    GEOMETRY_SURFACE = "Objects.Geometry.Surface"
    GEOMETRY_CURVE = "Objects.Geometry.Curve"