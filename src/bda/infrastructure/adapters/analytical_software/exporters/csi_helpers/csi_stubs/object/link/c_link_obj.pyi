class cLinkObj:

    def AddByPoint(
        self,
        Point1: str,
        Point2: str,
        Name: str,
        *,
        IsSingleJoint: bool = False,
        PropName: str = "Default",
        UserName: str = "",
    ) -> int:
        """
        This function adds a new link object whose end points are specified by name.

        Parameters
        ----------
        Point1 : str

            The name of a defined point object at the I-End of the added link object.

        Point2 : str

            The name of a defined point object at the J-End of the added link object.

            This item is ignored if the IsSingleJoint item is True.

        Name : str

            This is the name that the program ultimately assigns for the link object.
            If no UserName is specified, the program assigns a default name to the link object.
            If a UserName is specified and that name is not used for another link object,
            the UserName is assigned to the link object;
            otherwise a default name is assigned to the link object.

        IsSingleJoint : bool

            This item is True if a one-joint link is added and False if a two-joint link is added.

        PropName : str

            This is either Default or the name of a defined link property.

            If it is Default the program assigns a default link property to the link object.
            If it is the name of a defined link property, that property is assigned to the link object.

        UserName : str

            This is an optional user specified name for the link object.
            If a UserName is specified and that name is already used for another link object,
            the program ignores the UserName.

        Returns
        -------
        int
            0 if the link object is successfully added; otherwise it returns a nonzero value.
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
        This function assigns a local axis angle to link objects.

        Parameters
        ----------

        Name : str

            The name of an existing link object or group, depending on the value of the ItemType item.

        Ang : float

            This is the angle that the local 2 and 3 axes are rotated about the positive local 1 axis,
            from the default orientation or, if the Advanced item is True,
            from the orientation determined by the plane reference vector.
            The rotation for a positive angle appears counterclockwise
            when the local +1 axis is pointing toward you. [deg]

        ItemType : int

            This is one of the following items in the eItemType enumeration:

            Object = 0
            Group = 1
            SelectedObjects = 2

        If this item is Object, the assignment is made to the link object specified by the Name item.
        If this item is Group, the assignment is made to all link objects in the group specified by
        the Name item.
        If this item is SelectedObjects, assignment is made to all selected link objects,
        and the Name item is ignored.

        Returns
        -------
        int
            0 if the local axis angle is successfully assigned; otherwise it returns a nonzero value.
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
        This function adds or removes link objects from a specified group.

        Parameters
        ----------
        Name : str

            The name of an existing link object or group, depending on the value of the ItemType item.

        GroupName : str

            The name of an existing group to which the assignment is made.

        Remove : bool

            If this item is False, the specified link objects are added to the group
            specified by the GroupName item. If it is True, the link objects are removed from the group.

        ItemType : int

            This is one of the following items in the eItemType enumeration:

            Object = 0
            Group = 1
            SelectedObjects = 2

        If this item is Object, the link object specified by the Name item is added or
        removed from the group specified by the GroupName item.
        If this item is Group, all link objects in the group specified by the Name item
        are added or removed from the group specified by the GroupName item.
        If this item is SelectedObjects, all selected link objects are added or removed
        from the group specified by the GroupName item, and the Name item is ignored.

        Returns
        -------
        int
            0 if the group assignment is successful; otherwise it returns a nonzero value.

        """
        ...