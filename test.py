import hashlib

import zeep
from lxml import etree
from zeep.wsse import UsernameToken


class OpenClinicaClient(object):
    def __init__(self, username, password):
        password = hashlib.sha1(password.encode('utf-8')).hexdigest()

        self._client = zeep.Client(
            'https://tds-edc.com/rdpws/ws/study/v1/studyWsdl.wsdl',
            strict=False,
            wsse=UsernameToken(username, password=password))

    def get_studies(self):
        """Generator which yields a dict containing the study, site and
        metadata.

        """
        result = self._client.service.listAll()
        for study in result.studies.study:
            for site in study.sites.site:
                metadata = self.study_metadata(site.identifier)
                yield {
                    'study': study,
                    'site': site,
                    'metadata': metadata
                }

    def study_metadata(self, identifier):
        """Retrieve the getMetadata for a study.

        Note that the WSDL doesn't match the data returned by the SOAP server
        so we let zeep return the raw requests response and extract the
        odm node ourselves.

        :param identifier: The study identifier
        :return: The ODM document
        :rtype: lxml.etree._Element

        """
        with self._client.options(raw_response=True):
            response = self._client.service.getMetadata({
                'identifier': identifier
            })

            if response.status_code != 200:
                return None

            document = etree.fromstring(response.content)
            odm = document.xpath('//ns:odm', namespaces={
                'ns': 'http://openclinica.org/ws/study/v1'
            })
            if odm:
                odm_string = odm[0].text.encode('utf-8')
                return etree.fromstring(odm_string)


client = OpenClinicaClient('yyy', 'xxx')

for study in client.get_studies():
    print('Site: ', study['site'])
    print('Metadata:')
    print(etree.tostring(study['metadata'], pretty_print=True).decode('utf-8'))

