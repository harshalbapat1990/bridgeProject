class cGroupDef:
    def SetGroup(
        self,
        Name: str,
        *,
        color: int = -1,
        SpecifiedForSelection: bool = True,
        SpecifiedForSectionCutDefinition: bool = True,
        SpecifiedForSteelDesign: bool = True,
        SpecifiedForConcreteDesign: bool = True,
        SpecifiedForAluminumDesign: bool = True,
        SpecifiedForColdFormedDesign: bool = True,
        SpecifiedForStaticNLActiveStage: bool = True,
        SpecifiedForBridgeResponseOutput: bool = True,
        SpecifiedForAutoSeismicOutput: bool = False,
        SpecifiedForAutoWindOutput: bool = False,
        SpecifiedForMassAndWeight: bool = True,
    ) -> int:
        """
        Creates a new group or modifies an existing group.

        Parameters
        ----------
        Name : str
            Name of the group. If a group with this name already exists,
            its properties are modified. Otherwise, a new group is created.

        color : int, default=-1
            Display color assigned to the group.

            If set to ``-1``, CSI automatically selects a display color.

        SpecifiedForSelection : bool, default=True
            Indicates whether the group can be used for object selection.

        SpecifiedForSectionCutDefinition : bool, default=True
            Indicates whether the group can be used when defining
            section cuts.

        SpecifiedForSteelDesign : bool, default=True
            Indicates whether the group can be used for steel frame
            design assignments.

        SpecifiedForConcreteDesign : bool, default=True
            Indicates whether the group can be used for concrete frame
            design assignments.

        SpecifiedForAluminumDesign : bool, default=True
            Indicates whether the group can be used for aluminum frame
            design assignments.

        SpecifiedForColdFormedDesign : bool, default=True
            Indicates whether the group can be used for cold-formed
            steel frame design assignments.

        SpecifiedForStaticNLActiveStage : bool, default=True
            Indicates whether the group can be used to define stages
            in nonlinear static analyses.

        SpecifiedForBridgeResponseOutput : bool, default=True
            Indicates whether the group can be used for bridge response
            output reporting.

        SpecifiedForAutoSeismicOutput : bool, default=False
            Indicates whether the group can be used for reporting
            automatically generated seismic loads.

        SpecifiedForAutoWindOutput : bool, default=False
            Indicates whether the group can be used for reporting
            automatically generated wind loads.

        SpecifiedForMassAndWeight : bool, default=True
            Indicates whether the group can be used for reporting
            group mass and weight.

        Returns
        -------
        int
            Returns 0 if the group data is successfully assigned.
            Otherwise, returns a nonzero value indicating that an
            error occurred.
        """
        ...