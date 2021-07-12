from collections import namedtuple
from typing import List, NamedTuple, Optional, Tuple, Union

from pybliometrics.scopus.superclasses import Search
from pybliometrics.scopus.utils import check_integrity, check_parameter_value,\
    check_field_consistency, make_search_summary


class AffiliationSearch(Search):
    @property
    def affiliations(self) -> Optional[List[NamedTuple]]:
        """A list of namedtuples storing affiliation information,
        where each namedtuple corresponds to one affiliation.
        The information in each namedtuple is (eid name variant documents city
        country parent).

        All entries are strings or None.  Field "variant" combines variants
        of names with a semicolon.

        Raises
        ------
        ValueError
            If the elements provided in integrity_fields do not match the
            actual field names (listed above).
        """
        # Initiate namedtuple with ordered list of fields
        fields = 'eid name variant documents city country parent'
        aff = namedtuple('Affiliation', fields)
        check_field_consistency(self._integrity, fields)
        # Parse elements one-by-one
        out = []
        for item in self._json:
            name = item.get('affiliation-name')
            variants = [d.get('$', "") for d in item.get('name-variant', [])
                        if d.get('$', "") != name]
            new = aff(eid=item.get('eid'), variant=";".join(variants),
                      documents=item.get('document-count', '0'), name=name,
                      city=item.get('city'), country=item.get('country'),
                      parent=item.get('parent-affiliation-id'))
            out.append(new)
        # Finalize
        check_integrity(out, self._integrity, self._action)
        return out or None

    def __init__(self,
                 query: str,
                 refresh: Union[bool, int] = False,
                 download: bool = True,
                 count: int = 200,
                 integrity_fields: Union[List[str], Tuple[str, ...]] = None,
                 integrity_action: str = "raise",
                 verbose: bool = False
                 ) -> None:
        """Interaction with the Affiliation Search API.

        :param query: A string of the query.  For allowed fields and values see
                      https://dev.elsevier.com/sc_affil_search_tips.html.
        :param refresh: Whether to refresh the cached file if it exists or not.
                        If int is passed, cached file will be refreshed if the
                        number of days since last modification exceeds that value.
        :param count: The number of entries to be displayed at once.  A smaller
                      number means more queries with each query having
                      fewer results.
        :param download: Whether to download results (if they have not been
                         cached).
        :param integrity_fields: Names of fields whose completeness should
                                 be checked.  AffiliationSearch will perform
                                 the action specified in `integrity_action`
                                 if elements in these fields are missing.
                                 This helps avoiding idiosynchratically missing
                                 elements that should always be present
                                 (e.g. EID or name).
        :param integrity_action: What to do in case integrity of provided fields
                                 cannot be verified.  Possible actions:
                                 - "raise": Raise an AttributeError
                                 - "warn": Raise a UserWarning
        :param verbose: Whether to print a download progress bar.

        Raises
        ------
        ScopusQueryError
            If the number of search results exceeds 5000.

        ValueError
            If the integrity_action parameter is not one of the allowed ones.

        Notes
        -----
        The directory for cached results is `{path}/STANDARD/{fname}`,
        where  `path` is specified in your configuration file and `fname` is
        the md5-hashed version of `query`.
        """
        # Check
        allowed = ("warn", "raise")
        check_parameter_value(integrity_action, allowed, "integrity_action")

        # Query
        self._action = integrity_action
        self._integrity = integrity_fields or []
        self._query = query
        self._refresh = refresh
        self._view = "STANDARD"
        Search.__init__(self, query=query, api="AffiliationSearch",
                        count=count, download=download, verbose=verbose)

    def __str__(self):
        """Return a summary string."""
        res = [a['affiliation-name'] for a in self._json]
        return make_search_summary(self, "affiliation", res)
