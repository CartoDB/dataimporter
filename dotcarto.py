from os.path import join
from zipfile import ZipFile
from StringIO import StringIO

from carto.sql import SQLClient
from carto.auth import APIKeyAuthClient


class DotCartoFile(object):
    replacements = []
    visualization_id = None
    json = None

    def __init__(self, dotcarto_file, endpoint_base_url, api_key):
        self.dotcarto_file = dotcarto_file
        self.sql = SQLClient(APIKeyAuthClient(endpoint_base_url, api_key))

    def replace_dataset(self, original_dataset_name, new_dataset_name):
        self.replacements.append({
            "original_dataset_name": original_dataset_name,
            "new_dataset_name": new_dataset_name
        })

    def replace_datasets_in_dotcarto_file(self, zip_buffer):
        for replacement in self.replacements:
            original_dataset_name = replacement["original_dataset_name"]
            new_dataset_name = replacement["new_dataset_name"]

            self.json = self.json.replace(original_dataset_name, new_dataset_name)

            new_dataset = self.sql.send("select * from {dataset}".format(dataset=replacement["new_dataset_name"]), format="gpkg")
            zip_buffer.writestr(join(self.visualization_id, replacement["new_dataset_name"] + ".gpkg"), new_dataset)

    def get_new(self, destination_path=None):
        with ZipFile(self.dotcarto_file) as ninth_decimal_csv:
            self.visualization_id = ninth_decimal_csv.namelist()[0][:-1]
            json_file_relative_path = join(self.visualization_id, self.visualization_id + ".carto.json")
            self.json = ninth_decimal_csv.read(json_file_relative_path)

        if destination_path is not None:
            with ZipFile(destination_path, mode='w') as new_dotcarto_file:
                self.replace_datasets_in_dotcarto_file(new_dotcarto_file)
                new_dotcarto_file.writestr(json_file_relative_path, self.json.encode('utf-8'))
        else:
            new_dotcarto_buffer = StringIO()
            with ZipFile(new_dotcarto_buffer, mode='w') as new_dotcarto_file:
                self.replace_datasets_in_dotcarto_file(new_dotcarto_file)
                new_dotcarto_file.writestr(json_file_relative_path, self.json.encode('utf-8'))
            new_dotcarto_buffer.seek(0)
            return new_dotcarto_buffer
