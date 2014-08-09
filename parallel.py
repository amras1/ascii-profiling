import timeit
import time
from astropy.io import ascii
import pandas
import numpy as np
from astropy.table import Table, Column
from tempfile import NamedTemporaryFile
import random
import string
import matplotlib.pyplot as plt
import webbrowser

def make_table(table, size=10000, n_floats=10, n_ints=0, n_strs=0, float_format=None, str_val=None):
    if str_val is None:
        str_val = "abcde12345"
    cols = []
    for i in xrange(n_floats):
        dat = np.random.uniform(low=1, high=10, size=size)
        cols.append(Column(dat, name='f{}'.format(i)))
    for i in xrange(n_ints):
        dat = np.random.randint(low=-9999999, high=9999999, size=size)
        cols.append(Column(dat, name='i{}'.format(i)))
    for i in xrange(n_strs):
        if str_val == 'random':
            dat = np.array([''.join([random.choice(string.letters) for j in range(10)]) for k in range(size)])
        else:
            dat = np.repeat(str_val, size)
        cols.append(Column(dat, name='s{}'.format(i)))
    t = Table(cols)

    if float_format is not None:
        for col in t.columns.values():
            if col.name.startswith('f'):
                col.format = float_format

    t.write(table.name, format='ascii')

output_text = []

def plot_case(n_floats=10, n_ints=0, n_strs=0, float_format=None, str_val=None):
    global table1, output_text
    n_rows = (10000, 20000, 50000, 100000, 200000)  # include 200000 for publish run
    numbers = (1,     1,     1,       1,      1)
    repeats = (3,     2,     1,       1,      1)
    times_fast = []
    times_fast_parallel = []
    times_pandas = []
    for n_row, number, repeat in zip(n_rows, numbers, repeats):
        table1 = NamedTemporaryFile()
        make_table(table1, n_row, n_floats, n_ints, n_strs, float_format, str_val)
        t = timeit.repeat("ascii.read(table1.name, format='basic', guess=False, use_fast_converter=True)", 
                   setup='from __main__ import ascii, table1', number=number, repeat=repeat)
        times_fast.append(min(t) / number)
        t = timeit.repeat("ascii.read(table1.name, format='basic', guess=False, parallel=True, use_fast_converter=True)", 
                   setup='from __main__ import ascii, table1', number=number, repeat=repeat)
        times_fast_parallel.append(min(t) / number)
        t = timeit.repeat("pandas.read_csv(table1.name, sep=' ', header=0)", 
                   setup='from __main__ import table1, pandas', number=number, repeat=repeat)
        times_pandas.append(min(t) / number)
    plt.loglog(n_rows, times_fast, '-or', label='io.ascii Fast-c')
    plt.loglog(n_rows, times_fast_parallel, '-og', label='io.ascii Parallel Fast-c')
    plt.loglog(n_rows, times_pandas, '-oc', label='Pandas')
    plt.grid()
    plt.legend(loc='best')
    plt.title('n_floats={} n_ints={} n_strs={} float_format={} str_val={}'.format(
                            n_floats, n_ints, n_strs, float_format, str_val))
    plt.xlabel('Number of rows')
    plt.ylabel('Time (sec)')
    img_file = 'graph{}.png'.format(len(output_text) + 1)
    plt.savefig(img_file)
    plt.clf()
    text = 'Pandas to io.ascii Fast-C speed ratio: {:.2f} : 1<br/>'.format(times_fast[-1] / times_pandas[-1])
    text += 'io.ascii parallel to Pandas speed ratio: {:.2f} : 1'.format(times_pandas[-1] / times_fast_parallel[-1])
    output_text.append((img_file, text))

plot_case(n_floats=10, n_ints=0, n_strs=0)
plot_case(n_floats=10, n_ints=10, n_strs=10)
plot_case(n_floats=10, n_ints=10, n_strs=10, float_format='%.4f')
plot_case(n_floats=10, n_ints=0, n_strs=0, float_format='%.4f')
plot_case(n_floats=0, n_ints=0, n_strs=10)
plot_case(n_floats=0, n_ints=0, n_strs=10, str_val="'asdf asdfa'")
plot_case(n_floats=0, n_ints=0, n_strs=10, str_val="random")
plot_case(n_floats=0, n_ints=10, n_strs=0)

html_file = open('out.html', 'w')
html_file.write('<html><head><meta charset="utf-8"/><meta content="text/html;charset=UTF-8" http-equiv="Content-type"/>')
html_file.write('</html><body><h1 style="text-align:center;">Profile of io.ascii</h1>')
for img, descr in output_text:
    html_file.write('<img src="{}"><p style="font-weight:bold;">{}</p><hr>'.format(img, descr))
html_file.write('</body></html>')
html_file.close()
webbrowser.open('out.html')
