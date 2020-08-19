class PdbNotFoundError(LookupError):
    """PDB query returned a 404 Not Found"""

    def __init__(self, tag, pk):
        msg = f"pdb missing {tag}/{pk}"
        super().__init__(msg)
