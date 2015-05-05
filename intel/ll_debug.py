from pprint import pprint, pformat

def __debugvar__(var):
  f = open('/tmp/debugfile.txt', 'a')
  f.write(type(var).__name__ + ": " + pformat(var) + "\n")
  f.close()
