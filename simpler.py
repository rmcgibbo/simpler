import numpy as np
import sys
import rpy2.rinterface as ri
import rpy2.robjects as ro
from rpy2.robjects.numpy2ri import numpy2ri
ro.conversion.py2ri = numpy2ri
from IPython.extensions.rmagic import RInterpreterError, Rconverter
from IPython.utils.py3compat import str_to_unicode, unicode_to_str, PY3
 
__all__ = ['r']
 
class _RMagic(object):
    """
    Stripped down version of IPython's RMagic, suitable for use
    outside of ipython.
    """
    def __init__(self, pyconverter=np.asarray):
        self._Rstdout_cache = []
        self._r = ro.R()
        self._pyconverter = pyconverter
        self._Rconverter = Rconverter
    
    def push(self, **kwargs):
        """Send values to the R interpreter
        
        Usage
        -----
        >>> r.push(a=12)  # set r's a equal to 1
        >>> r.eval('print(a)')
        [1] 12
        """
        for k,v in kwargs.iteritems():
            self._r.assign(k, self._pyconverter(v))
            
    def get(self, key, as_dataframe=True):
        """Get a value from the R interpreter
        
        Parameters
        ----------
        key : str
            The name of the varaible to pull from r
            
        Usage
        -----
        >>> r.push(a=12)
        >>> print r.get('a')
        [12]
        """
        return self._Rconverter(self._r[key], dataframe=as_dataframe)
 
 
    def eval(self, line):
        """Evaluate a line or block of code in R
        
        Parameters
        ----------
        line : str
            The code to execute
        
        Examples
        --------
        >>> r.eval('''
        ... x = 1:5
        ... df = data.frame(x=x, y=x^2)
        ... print(df)
        ... ''')
          x  y
        1 1  1
        2 2  4
        3 3  9
        4 4 16
        5 5 25
        """
        old_writeconsole = ri.get_writeconsole()
        ri.set_writeconsole(self._write_console)
        try:
            value = ri.baseenv['eval'](ri.parse(line))
        except (ri.RRuntimeError, ValueError) as exception:
            warning_or_other_msg = self._flush() # otherwise next return seems to have copy of error
            raise RInterpreterError(line, str_to_unicode(str(exception)), warning_or_other_msg)
        text_output = self._flush()
        ri.set_writeconsole(old_writeconsole)
        
        if text_output:
            sys.stdout.write(unicode_to_str(text_output, 'utf-8'))
    
    def _write_console(self, output):
        '''
        A hook to capture R's stdout in a cache.
        '''
        self._Rstdout_cache.append(output)
    
    def _flush(self):
        '''
        Flush R's stdout cache to a string, returning the string.
        '''
        value = ''.join([str_to_unicode(s, 'utf-8') for s in self._Rstdout_cache])
        self._Rstdout_cache = []
        return value
 
# create an instance of the class that can be imported
r = _RMagic()
    
if __name__ == '__main__':
    x = np.arange(10)
    r.push(x=x)
    r.eval('''
    library(ggplot2)
    df = data.frame(x=x, y=x^2)
    ggplot(data=df, aes(x=x, y=y)) + geom_line()
    ggsave('plot.png')
    system('open plot.png')
    ''')
