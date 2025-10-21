Added mitigation code to the "zhmc nic create" and "zhmc nic update" commands
to deal with the following HMC defects that occurred with NICs backed by
Hipersocket adapters on z17 CPCs:

* The specified NIC name was ignored by the HMC when creating or updating the
  NIC and a name was specified. This is mitigated by explicitly updating the
  name.

* When the "Create NIC" operation performed by "zhmc nic create" results in
  HTTP 500,0 with "Invalid UUID string:", the NIC was nevertheless created.
  This is mitigated by ignoring that specific error and looking up the new NIC
  by comparing the new list of NICs on the partition with the prior list of
  NICs.
