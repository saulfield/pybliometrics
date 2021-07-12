from collections import namedtuple
from typing import List, NamedTuple, Optional, Union

from pybliometrics.scopus.superclasses import Retrieval
from pybliometrics.scopus.utils import check_parameter_value


class PlumXMetrics(Retrieval):
    @property
    def category_totals(self) -> Optional[List[NamedTuple]]:
        """A list of namedtuples representing total metrics as categorized
        by PlumX Metrics in the form (capture, citation, mention, socialMedia,
        usage).

        Note: For Citation category a maximum citation count across sources is
        shown.  For details on PlumX Metrics categories see
        https://plumanalytics.com/learn/about-metrics/.
        """
        out = []
        fields = 'name total'
        cat = namedtuple('Category', fields)
        for item in self._json.get('count_categories', []):
            if item.get('name') and item.get('total'):
                new = cat(name=item.get('name'),
                          total=item.get('total'))
                out.append(new)
        return out or None

    @property
    def capture(self) -> Optional[List[NamedTuple]]:
        """A list of namedtuples representing metrics in the Captures category.

        Note: For details on Capture metrics see
        https://plumanalytics.com/learn/about-metrics/capture-metrics/.
        """
        categories = self._json.get('count_categories', [])
        mention_metrics = _category_metrics('capture', categories)
        return _list_metrics_totals(mention_metrics) or None

    @property
    def citation(self) -> Optional[List[NamedTuple]]:
        """A list of namedtuples representing citation counts from
        different sources.

        Note: For details on Citation metrics see
        https://plumanalytics.com/learn/about-metrics/citation-metrics/.
        """
        categories = self._json.get('count_categories', [])
        citation_metrics = _category_metrics('citation', categories)
        source_metrics = []
        if citation_metrics:
            for item in citation_metrics:
                if item.get('sources'):
                    source_metrics += item.get('sources')
        return _list_metrics_totals(source_metrics) or None

    @property
    def mention(self) -> Optional[List[NamedTuple]]:
        """A list of namedtuples representing metrics in Mentions category.

        Note: For details on Mention metrics see
        https://plumanalytics.com/learn/about-metrics/mention-metrics/.
        """
        categories = self._json.get('count_categories', [])
        mention_metrics = _category_metrics('mention', categories)
        return _list_metrics_totals(mention_metrics) or None

    @property
    def social_media(self) -> Optional[List[NamedTuple]]:
        """A list of namedtuples representing social media metrics.

        Note: For details on Social Media metrics see
        https://plumanalytics.com/learn/about-metrics/social-media-metrics/.
        """
        categories = self._json.get('count_categories', [])
        social_metrics = _category_metrics('socialMedia', categories)
        return _list_metrics_totals(social_metrics) or None

    @property
    def usage(self) -> Optional[List[NamedTuple]]:
        """A list of namedtuples representing Usage category metrics.

        Note: For details on Usage metrics see
        https://plumanalytics.com/learn/about-metrics/usage-metrics/.
        """
        categories = self._json.get('count_categories', [])
        usage_metrics = _category_metrics('usage', categories)
        return _list_metrics_totals(usage_metrics) or None

    def __init__(self,
                 identifier: str,
                 id_type: str,
                 refresh: Union[bool, int] = False
                 ) -> None:
        """Interaction with the PlumX Metrics API.

        :param identifier: The identifier of a document.
        :param id_type: The type of used ID. Allowed values are:
                        - 'airitiDocId'
                        - 'arxivId'
                        - 'cabiAbstractId'
                        - 'citeulikeId'
                        - 'digitalMeasuresArtifactId'
                        - 'doi'
                        - 'elsevierId'
                        - 'elsevierPii'
                        - 'facebookCountUrlId'
                        - 'figshareArticleId'
                        - 'githubRepoId'
                        - 'isbn'
                        - 'lccn'
                        - 'medwaveId'
                        - 'nctId'
                        - 'oclc'
                        - 'pittEprintDscholarId'
                        - 'pmcid'
                        - 'pmid'
                        - 'redditId'
                        - 'repecHandle'
                        - 'repoUrl'
                        - 'scieloId'
                        - 'sdEid'
                        - 'slideshareUrlId'
                        - 'smithsonianPddrId'
                        - 'soundcloudTrackId'
                        - 'ssrnId'
                        - 'urlId'
                        - 'usPatentApplicationId'
                        - 'usPatentPublicationId'
                        - 'vimeoVideoId'
                        - 'youtubeVideoId'
        :param refresh: Whether to refresh the cached file if it exists or not.
                        If int is passed, cached file will be refreshed if the
                        number of days since last modification exceeds that value.

        Notes
        -----
        The directory for cached results is `{path}/ENHANCED/{identifier}`,
        where `path` is specified in your configuration file.
        """
        # Checks
        allowed = ('airitiDocId', 'arxivId', 'cabiAbstractId',
                   'citeulikeId', 'digitalMeasuresArtifactId', 'doi',
                   'elsevierId', 'elsevierPii', 'facebookCountUrlId',
                   'figshareArticleId', 'githubRepoId', 'isbn',
                   'lccn', 'medwaveId', 'nctId', 'oclc',
                   'pittEprintDscholarId', 'pmcid', 'pmid', 'redditId',
                   'repecHandle', 'repoUrl', 'scieloId', 'sdEid',
                   'slideshareUrlId', 'smithsonianPddrId', 'soundcloudTrackId',
                   'ssrnId', 'urlId', 'usPatentApplicationId',
                   'usPatentPublicationId', 'vimeoVideoId', 'youtubeVideoId')
        check_parameter_value(id_type, allowed, "id_type")
        self._id_type = id_type
        self._identifier = identifier

        # Load json
        self._refresh = refresh
        self._view = 'ENHANCED'
        Retrieval.__init__(self, identifier=identifier, id_type=id_type,
                           api='PlumXMetrics')

    def __str__(self):
        """Print a summary string."""
        s = f"Document with {self._id_type} {self._identifier} received:\n- "
        cats = [f"{c.total:,} citation(s) in category '{c.name}'"
                for c in self.category_totals]
        s += "\n- ".join(cats)
        s += f"\nas of {self.get_cache_file_mdate().split()[0]}"
        return s


def _category_metrics(category_name, categories_list):
    """Auxiliary function returning all available metrics in a single
    category as a list of dicts
    """
    cat_counts = []
    for item in categories_list:
        if item.get('name') == category_name:
            cat_counts += item.get('count_types', [])
    return cat_counts


def _list_metrics_totals(metric_counts):
    """Formats list of dicts of metrics into list of namedtuples in form
    (name, total)
    """
    out = []
    # Metric names and associated counts if either is not None
    values = [[m.get('name'), m.get('total')] for m in metric_counts
              if m.get('name') and m.get('total')]
    fields = 'name total'
    capture = namedtuple('Metric', fields)
    for v in values:
        new = capture(name=v[0], total=v[1])
        out.append(new)
    return out
