import pickle

class Roman2num:
    def __init__(self, fname):
        self.int2roman = {}
        self.roman2int = {}
        self.fname = fname
        self.outfname = fname + '.pk'
        
    def build_table(self):
        try:
            self.f = open(self.fname, 'r')
            lines = self.f.readlines()
            for t in lines:
                if ':' not in t: continue
                items = t.split(':')
                items = [x.strip() for x in items]
                rank = int(items[0])
                roman_numeral = items[1]
                self.int2roman[rank] = roman_numeral
                self.roman2int[roman_numeral] = rank
            self.f.close()
        except Exception as e:
            print(f"Error reading {self.fname}: {e}")
        
    def write_table(self):
        try:
            self.outf = open(self.outfname, 'wb')
            pickle.dump(self.int2roman, self.outf)
            pickle.dump(self.roman2int, self.outf)
            self.outf.close()
            print(f"Successfully created {self.outfname}")
        except Exception as e:
            print(f"Error writing pickle: {e}")
        
if __name__ == "__main__":
    r = Roman2num('roman.txt')
    r.build_table()
    r.write_table()