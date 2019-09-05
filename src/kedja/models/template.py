import os
from logging import getLogger
from pathlib import Path

from kedja.interfaces import ITemplateFileUtil
from kedja.models.export_import import EXPORT_VERSION
# from kedja.utils import utcnow
from pyramid.exceptions import ConfigurationError
from yaml import safe_dump, safe_load
from zope.interface import implementer


logger = getLogger(__name__)


@implementer(ITemplateFileUtil)
class TemplateFileUtil(object):
    """ Util to handle template files. """

    def __init__(self, registry):
        self.registry = registry
        self.tpl_dir = registry.settings['kedja.templates_dir']

    def read_appstruct(self, file_stem):
        fp = self._fp(file_stem)
        with open(fp, 'r') as stream:
            result = safe_load(stream)
        return result

    def remove(self, file_stem):
        if file_stem in self.get_existing_filestems():
            fp = self._fp(file_stem)
            os.remove(fp)

    def write(self, appstruct):
        assert 'export' in appstruct
        assert appstruct['version'] == EXPORT_VERSION
        assert isinstance(appstruct['title'], str)
        file_stem = str(appstruct['id'])
        fp = self._fp(file_stem)
        with open(fp, 'w') as fb:
            safe_dump(appstruct, stream=fb, default_flow_style=False)
        return file_stem

    def get_all_appstructs(self):
        for x in self.get_existing_filestems():
            yield self.read_appstruct(x)

    def get_existing_filestems(self):
        # stem / name / suffix
        return list(x.stem for x in self._path.glob('*.yaml'))

    @property
    def _path(self):
        return Path(self.tpl_dir)

    def _fp(self, file_stem:str):
        if '.' in file_stem:  # pragma: no cover
            raise ValueError("'file_stem' can't contain dots.")
        return os.path.join(self.tpl_dir, "%s.yaml" % file_stem)


def includeme(config):
    # Check templates dir
    tpl_dir = config.registry.settings.get('kedja.templates_dir', None)
    if tpl_dir:
        path = Path(tpl_dir)
        if not path.exists():
            logger.debug("'kedja.templates_dir' doesn't exist at %r, creating...", tpl_dir)
            path.mkdir()
    else:
        if config.registry.package_name == 'testing':
            logger.debug("'kedja.templates_dir' not present in configuration.")
            # Don't care about this during testing
            return
        raise ConfigurationError("'kedja.templates_dir' must exist in paster.ini file.")

    fh_util = TemplateFileUtil(config.registry)
    config.registry.registerUtility(fh_util)
