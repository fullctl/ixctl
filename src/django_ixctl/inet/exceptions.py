class PdbNotFoundError(LookupError):
    """PDB query returned a 404 Not Found"""

    def __init__(self, tag, pk):
        msg = "pdb missing {}/{}".format(tag, pk)
        super(PdbNotFoundError, self).__init__(msg)
