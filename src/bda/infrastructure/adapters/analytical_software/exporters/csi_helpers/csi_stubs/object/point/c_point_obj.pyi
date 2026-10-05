from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.csi_stubs.c_sap_model import DofVector, \
    LinearLinkStiffnessVector


class cPointObj:

    def AddCartesian(
        self,
        X: float,
        Y: float,
        Z: float,
        Name: str,
        *,
        UserName: str = "",
        CSys: str = "Global",
        MergeOff: bool = False,
        MergeNumber: int = 0,
    ) -> int:
        """
        Add a point object to the model.

        Parameters
        ----------
        X : float
            X-coordinate in the specified coordinate system.

        Y : float
            Y-coordinate in the specified coordinate system.

        Z : float
            Z-coordinate in the specified coordinate system.

        Name : str
            This is the name that the program ultimately assigns for the point object.
            If no UserName is specified, the program assigns a default name to the point object.
            If a UserName is specified and that name is not used for another point,
            the UserName is assigned to the point; otherwise a default name is assigned to the point.

        UserName : str, default=""
            Optional user-defined point name.

        CSys : str, default="Global"
            Coordinate system in which the coordinates are defined.

        MergeOff : bool, default=False
            If False, coincident points may be merged.

        MergeNumber : int, default=0
            Merge identifier used when determining whether
            coincident points should merge.

        Returns
        -------
        tuple[int, str]

            ret_code : int
                CSI return code.
                0 indicates success.

            point_name : str
                Final point name assigned by CSI.
        """
        ...

    def SetRestraint(
        self,
        Name: str,
        Value: DofVector,
        *,
        ItemType: int = 0,
    ) -> int:
        """
        This function assigns the restraint assignments for a point object.
        The restraint assignments are always set in the point local coordinate system.

        Parameters
        ----------

        Name : str

            The name of an existing point object or group depending on the value of the ItemType item.

        Value: DofVector
            This is an array of six restraint values.
            Value(0) = U1
            Value(1) = U2
            Value(2) = U3
            Value(3) = R1
            Value(4) = R2
            Value(5) = R3

        ItemType : int, default=0

            This is one of the following items in the eItemType enumeration:
            Object = 0
            Group = 1
            SelectedObjects = 2

        Returns
        -------
        int
        The function returns zero if the restraint assignments are successfully assigned,
        otherwise it returns a nonzero value.

        """
        ...

    def SetSpring(
        self,
        Name: str,
        K: LinearLinkStiffnessVector,
        *,
        ItemType: int = 0,
        IsLocalCSys: bool = True,
        Replace: bool = True,
    ) -> int:
        """
        This function assigns coupled springs to a point object.

        Parameters
        ----------

        Name : str,
            The name of an existing point object or group depending on the value of the ItemType item.

        K : LinearLinkStiffnessVector
            This is an array of six spring stiffness values.
            Value(0) = U1 [F/L]
            Value(1) = U2 [F/L]
            Value(2) = U3 [F/L]
            Value(3) = R1 [FL/rad]
            Value(4) = R2 [FL/rad]
            Value(5) = R3 [FL/rad]

        ItemType : int, default=0

            This is one of the following items in the eItemType enumeration:

            Object = 0
            Group = 1
            SelectedObjects = 2

            If this item is Object, the spring assignment is made to the point object specified by the Name item.
            If this item is Group, the spring assignment is made to all point objects in the group specified by the Name item.
            If this item is SelectedObjects, the spring assignment is made to all selected point objects and the Name item is ignored.

        IsLocalCSys : boolean, default=True

            If this item is True, the specified spring assignments are in the point object local coordinate system. If it is False, the assignments are in the Global coordinate system.

        Replace : boolean, default=False

            If this item is True, all existing point spring assignments to the specified point object(s) are deleted prior to making the assignment. If it is False, the spring assignments are added to any existing assignments.

        Returns
        -------
        int
            0 indicates success. A nonzero value indicates failure.
        """
        ...

    def SetLocalAxes(
        self,
        Name: str,
        A: float,
        B: float,
        C: float,
        *,
        ItemType: int = 0,
    ) -> int:
        """
        Assign local axis orientation to point objects.

        The local point coordinate system is initially aligned with
        the global coordinate system and then rotated in the following order:

        1. Rotate about the local 3-axis by angle ``a``.
        2. Rotate about the resulting local 2-axis by angle ``b``.
        3. Rotate about the resulting local 1-axis by angle ``c``.

        Parameters
        ----------
        Name : str
            Point object name or group name, depending on ``ItemType``.

        A : float
            Rotation about local 3-axis [deg].

        B : float
            Rotation about resulting local 2-axis [deg].

        C : float
            Rotation about resulting local 1-axis [deg].

        ItemType : eItemType, default=eItemType.Object
            Assignment target.

            - Object (0): assign to the specified point object.
            - Group (1): assign to all points in the specified group.
            - SelectedObjects (2): assign to all currently selected points.

        Returns
        -------
        int
            CSI return code.
            0 indicates success.
        """
        ...

