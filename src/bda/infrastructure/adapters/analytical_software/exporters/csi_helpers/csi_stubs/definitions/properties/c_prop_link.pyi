from bda.infrastructure.adapters.analytical_software.exporters.csi_helpers.csi_stubs.c_sap_model import DofVector, \
    FixityVector, LinearLinkStiffnessVector, LinearLinkDampingVector


class cPropLink:

    def SetLinear(
        self,
        Name: str,
        DOF: DofVector,
        Fixed: FixityVector,
        Ke: LinearLinkStiffnessVector,
        Ce: LinearLinkDampingVector,
        DJ2: float,
        DJ3: float,
        *,
        KeCoupled: bool = False,
        CeCoupled: bool = False,
        Notes: str = "",
        GUID: str = "",
    ) -> int:
        """
       Creates or modifies a linear link property.

       Parameters
       ----------
       Name : str
           Name of an existing or new link property. If the property
           already exists, it is modified. Otherwise, a new property
           is created.

       DOF : DofVector
           Degrees of freedom activated for the link property.

           Order:
           (U1, U2, U3, R1, R2, R3)

           A value of ``True`` indicates that the corresponding degree
           of freedom is active.

       Fixed : FixityVector
           Fixity state for each active degree of freedom.

           Order:
           (U1, U2, U3, R1, R2, R3)

           For active degrees of freedom:

           - ``True`` = fixed (restrained)
           - ``False`` = spring-supported

       Ke : LinearLinkStiffnessVector
           Uncoupled stiffness values for the link property.

           Order:
           (U1, U2, U3, R1, R2, R3)

           Units:

           - U1, U2, U3 : [F/L]
           - R1, R2, R3 : [FL]

           If ``KeCoupled`` is ``True``, CSI expects a coupled
           stiffness matrix containing 21 terms.

       Ce : LinearLinkDampingVector
           Uncoupled damping values for the link property.

           Order:
           (U1, U2, U3, R1, R2, R3)

           Units:

           - U1, U2, U3 : [F/L]
           - R1, R2, R3 : [FL]

           If ``CeCoupled`` is ``True``, CSI expects a coupled
           damping matrix containing 21 terms.

       DJ2 : float
           Distance from the J-end of the link to the U2 shear spring.
           Applies only when the U2 degree of freedom is active. [L]

       DJ3 : float
           Distance from the J-end of the link to the U3 shear spring.
           Applies only when the U3 degree of freedom is active. [L]

       KeCoupled : bool, default=False
           Indicates whether the stiffness definition is coupled.

           - False = 6 uncoupled stiffness terms
           - True = 21 coupled stiffness terms

       CeCoupled : bool, default=False
           Indicates whether the damping definition is coupled.

           - False = 6 uncoupled damping terms
           - True = 21 coupled damping terms

       Notes : str, default=""
           Optional notes assigned to the link property.

       GUID : str, default=""
           Global unique identifier assigned to the property.

           If set to ``"Default"``, CSI automatically generates
           a GUID.

       Returns
       -------
       int
           Returns 0 if the link property is successfully initialized.
           Otherwise, returns a nonzero value indicating that an
           error occurred.

       Notes
       -----
       This function initializes a linear link property. If called
       for an existing property, all previously defined property
       settings are reset to their default values before the new
       values are assigned.
       """