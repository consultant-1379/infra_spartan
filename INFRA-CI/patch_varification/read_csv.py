import csv

DATABASE_FILE = '/var/tmp/database_file/hardware.csv'
class read_csv_file():
    """
    Read CSV file and return date with Dictionatry
    """
    def __init__(self, type_file):
        self.type_f = type_file
    def check_read_file(self,):
        """
	Check the type, read the csv file
        """
        if self.type_f == 'hwfile':
             return self.read_csv_file_hw()
    def read_csv_file_hw(self):
        """
        read the file and return dictionary
        """
        with open(DATABASE_FILE,'r')as file_csv:
            data = csv.reader(file_csv)
            fields_names = data.next()
            file_data = {}
            for row in data:
                row = [i.strip() for i in row]
                j = ''
		for i in row:
                    index_value = row.index(i)
                    if index_value  == 0:
                        j = i
                        file_data[j] = {}
                        next
                    file_data[j][fields_names[index_value]] = i
            file_data1 = {}
            for i in file_data.keys():
		format_keys = file_data[i]['IP_Address']
                file_data1[format_keys] = file_data[i]
        return file_data1 
