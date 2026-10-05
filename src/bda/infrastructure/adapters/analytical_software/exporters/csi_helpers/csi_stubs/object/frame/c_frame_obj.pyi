class cFrameObj:

    def SetSection(
        self,
        Name: str,
        PropName: str,
        *,
        ItemType: int = 0,
        SVarTotalLength: float = 0.0,
        SVarRelStartLoc: float = 0.0,
    ) -> int:
        """
        Assign a frame section property to one or more frame objects.

        Parameters
        ----------
        Name : str
            Frame object name or group name, depending on ``ItemType``.

        PropName : str
            Frame section property name.
            Use "None" to clear the assignment.

        ItemType : eItemType, default=eItemType.Object
            Assignment target.

            - Object (0): assign to a single frame object.
            - Group (1): assign to all frame objects in a group.
            - SelectedObjects (2): assign to all selected frame objects.

        sVarRelStartLoc : float, default=0.0
            Relative distance along a nonprismatic section to the
            I-End (start) of the frame object.

            Ignored when ``sVarTotalLength == 0.0``.

        sVarTotalLength : float, default=0.0
            Total assumed nonprismatic section length.

            A value of ``0.0`` indicates that the nonprismatic section
            length is equal to the frame object length.

        Returns
        -------
        int
            CSI return code.

            - 0 = success
            - nonzero = error
        """
        ...

    def AddByPoint(
        self,
        Point1: str,
        Point2: str,
        Name: str,
        PropName: str,
        *,
        UserName: str = "",
    ) -> int:
        """
        This function adds a new frame object whose end points are specified by name.

        Parameters
        ----------
        Point1 : str

            The name of a defined point object at the I-End of the added frame object.

        Point2 : str

            The name of a defined point object at the J-End of the added frame object.

        Name : str

            This is the name that the program ultimately assigns for the frame object.
            If no UserName is specified, the program assigns a default name to the frame object.
            If a UserName is specified and that name is not used for another frame, cable or tendon object,
            the UserName is assigned to the frame object, otherwise a default name is assigned
            to the frame object.

        PropName : str

            This is Default, None, or the name of a defined frame section property.

            If it is Default, the program assigns a default section property to the frame object.
            If it is None, no section property is assigned to the frame object. If it is the name
            of a defined frame section property, that property is assigned to the frame object.

        UserName : str

            This is an optional user specified name for the frame object.
            If a UserName is specified and that name is already used for another frame object,
            the program ignores the UserName.

        Returns
        -------
        int
            0 if the frame object is successfully added, otherwise it returns a nonzero value.
        """
        ...

    def SetLocalAxes(
        self,
        Name: str,
        Ang: float,
        *,
        ItemType: int = 0,
    ) -> int:
        """
        Assign local axis orientation to frame objects.

        The local frame coordinate system is initially aligned with
        the global coordinate system and then rotated in the following order:

        1. Rotate about the local 3-axis by angle ``Ang``.
        2. Rotate about the resulting local 2-axis by angle ``0``.
        3. Rotate about the resulting local 1-axis by angle ``0``.

        Parameters
        ----------
        Name : str
            Frame object name or group name, depending on ``ItemType``.

        Ang : float
            Rotation about local 3-axis [deg].

        ItemType : eItemType, default=eItemType.Object
            Assignment target.

            - Object (0): assign to the specified frame object.
            - Group (1): assign to all frames in the specified group.
            - SelectedObjects (2): assign to all currently selected frames.
        """

    def SetInsertionPoint_1(
        self,
        Name: str,
        CardinalPoint: int,
        Mirror2: bool,
        Mirror3: bool,
        StiffTransform: bool,
        Offset1: tuple | list,
        Offset2: tuple | list,
        *,
        CSys: str = "Local",
        ItemType: int = 0,
    ) -> int:
        """
        This function assigns frame object insertion point data.
        The assignments include the cardinal point and end joint offsets.

        Parameters
        ----------

        Name : str

            The name of an existing frame object or group, depending on the value of the ItemType item.

        CardinaPoint : int

            This is a numeric value from 1 to 11 that specifies the cardinal point for the frame object. The cardinal point specifies the relative position of the frame section on the line representing the frame object.

            1 = bottom left
            2 = bottom center
            3 = bottom right
            4 = middle left
            5 = middle center
            6 = middle right
            7 = top left
            8 = top center
            9 = top right
            10 = centroid
            11 = shear center

        Mirror2 : bool

            If this item is True, the frame object section is assumed to be mirrored (flipped)
            about its local 2-axis.

        Mirror3 : bool

            If this item is True, the frame object section is assumed to be mirrored (flipped)
            about its local 3-axis.

        StiffTransform : bool

            If this item is True, the frame object stiffness is transformed for cardinal point
            and joint offsets from the frame section centroid.

        Offset1 : tuple | list

            This is an array of three joint offset distances, in the coordinate directions
            specified by CSys, at the I-End of the frame object. [L]

            Offset1(0) = Offset in the 1-axis or X-axis direction
            Offset1(1) = Offset in the 2-axis or Y-axis direction
            Offset1(2) = Offset in the 3-axis or Z-axis direction

        Offset2 : tuple | list

            This is an array of three joint offset distances, in the coordinate directions
            specified by CSys, at the J-End of the frame object. [L]

            Offset2(0) = Offset in the 1-axis or X-axis direction
            Offset2(1) = Offset in the 2-axis or Y-axis direction
            Offset2(2) = Offset in the 3-axis or Z-axis direction

        CSys : str

            This is Local or the name of a defined coordinate system. It is the coordinate
            system in which the Offset1 and Offset2 items are specified.

        ItemType : int

            This is one of the following items in the eItemType enumeration:

            Object = 0
            Group = 1
            SelectedObjects = 2

            If this item is Object, the assignment is made to the frame object specified
            by the Name item.

            If this item is Group, the assignment is made to all frame objects in
            the group specified by the Name item.

            If this item is SelectedObjects, assignment is made to all selected frame objects,
            and the Name item is ignored.

        Returns
        -------
        int
            0 if the insertion point data is successfully assigned, otherwise it returns a nonzero value.
        """
        ...

    def SetGroupAssign(
        self,
        Name: str,
        GroupName: str,
        *,
        Remove: bool = False,
        ItemType: int = 0,
    ) -> int:
        """
        This function adds or removes frame objects from a specified group.

        Parameters
        ----------

        Name : str

            The name of an existing frame object or group, depending on the value of the ItemType item.

        GroupName : str

            The name of an existing group to which the assignment is made.

        Remove : bool

            If this item is False, the specified frame objects are added to
            the group specified by the GroupName item. If it is True,
            the frame objects are removed from the group.

        ItemType : int

            This is one of the following items in the eItemType enumeration:

            Object = 0
            Group = 1
            SelectedObjects = 2

            If this item is Object, the frame object specified by the Name item is
            added or removed from the group specified by the GroupName item.
            If this item is Group, all frame objects in the group specified by
            the Name item are added or removed from the group specified by the GroupName item.
            If this item is SelectedObjects, all selected frame objects are added
            or removed from the group specified by the GroupName item, and the Name item is ignored.
            The function returns zero if the group assignment is successful,
            otherwise it returns a nonzero value.

        Returns
        -------
        int
            0 if the group assignment is successful, otherwise it returns a nonzero value.
        """
        ...

    def SetReleases(
            self,
            Name: str,
            II: tuple[bool] | list[bool],
            JJ: tuple[bool] | list[bool],
            StartValue: tuple[float] | list[float],
            EndValue: tuple[float] | list[float],
            *,
            ItemType: int = 0,
    ) -> int:
        """
        Assigns end releases and partial fixity springs to frame objects.

        Parameters
        ----------
        Name : str
            Name of an existing frame object or group, depending on
            the value of ``ItemType``.

        II, JJ : tuple[bool] | list[bool]
            Sequences of six boolean values defining releases at the
            I-end and J-end of the frame object.

            - [0] = U1 release
            - [1] = U2 release
            - [2] = U3 release
            - [3] = R1 release
            - [4] = R2 release
            - [5] = R3 release

        StartValue, EndValue : tuple[float] | list[float]
            Sequences of six partial fixity spring stiffness values
            assigned at the I-end and J-end of the frame object.

            - [0] = U1 partial fixity [F/L]
            - [1] = U2 partial fixity [F/L]
            - [2] = U3 partial fixity [F/L]
            - [3] = R1 partial fixity [FL/rad]
            - [4] = R2 partial fixity [FL/rad]
            - [5] = R3 partial fixity [FL/rad]

            Partial fixity values are applied only to released degrees
            of freedom.

        ItemType : int, default=0
            Assignment target.

            - 0 = Object
            - 1 = Group
            - 2 = SelectedObjects

            If ``ItemType`` is:

            - ``Object``, the assignment is made to the frame object
              specified by ``Name``.
            - ``Group``, the assignment is made to all frame objects
              in the group specified by ``Name``.
            - ``SelectedObjects``, the assignment is made to all
              currently selected frame objects and ``Name`` is ignored.

        Returns
        -------
        int
            Returns 0 if the releases and partial fixity assignments
            are successfully assigned. Otherwise, returns a nonzero
            value indicating that an error occurred.

        Notes
        -----
        Some release assignments may cause structural instability.
        In such cases, an error is returned.

        Examples of unstable release configurations include:

        - U1 released at both ends.
        - U2 released at both ends.
        - U3 released at both ends.
        - R1 released at both ends.
        - R2 released at both ends and U3 released at either end.
        - R3 released at both ends and U2 released at either end.
        """
        ...
