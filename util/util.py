import collections
import copy
import datetime
import gc
import time

# import torch
import numpy as np

from util.logconf import logging
log = logging.getLogger(__name__)
# log.setLevel(logging.WARN)
# log.setLevel(logging.INFO)
log.setLevel(logging.DEBUG)

IrcTuple = collections.namedtuple('IrcTuple', ['index', 'row', 'col'])
XyzTuple = collections.namedtuple('XyzTuple', ['x', 'y', 'z'])

def xyz2irc(coord_xyz, origin_xyz, vxSize_xyz, direction_tup):
    # Note: _cri means Col,Row,Index
    if direction_tup == (1, 0, 0, 0, 1, 0, 0, 0, 1):
        direction_ary = np.ones((3,))
    elif direction_tup == (-1, 0, 0, 0, -1, 0, 0, 0, 1):
        direction_ary = np.array((-1, -1, 1))
    else:
        raise Exception("Unsupported direction_tup: {}".format(direction_tup))

    coord_cri = (np.array(coord_xyz) - np.array(origin_xyz)) / np.array(vxSize_xyz)
    coord_cri *= direction_ary
    return IrcTuple(*list(reversed(coord_cri.tolist())))

def irc2xyz(coord_irc, origin_xyz, vxSize_xyz, direction_tup):
    # Note: _cri means Col,Row,Index
    coord_cri = np.array(list(reversed(coord_irc)))
    coord_xyz = coord_cri * np.array(vxSize_xyz) + np.array(origin_xyz)
    return XyzTuple(*coord_xyz.tolist())


def importstr(module_str, from_=None):
    """
    >>> importstr('os')
    <module 'os' from '.../os.pyc'>
    >>> importstr('math', 'fabs')
    <built-in function fabs>
    """
    if from_ is None and ':' in module_str:
        module_str, from_ = module_str.rsplit(':')

    module = __import__(module_str)
    for sub_str in module_str.split('.')[1:]:
        module = getattr(module, sub_str)

    if from_:
        try:
            return getattr(module, from_)
        except:
            raise ImportError('{}.{}'.format(module_str, from_))
    return module


# class dotdict(dict):
#     '''dict where key can be access as attribute d.key -> d[key]'''
#     @classmethod
#     def deep(cls, dic_obj):
#         '''Initialize from dict with deep conversion'''
#         return cls(dic_obj).deepConvert()
#
#     def __getattr__(self, attr):
#         if attr in self:
#             return self[attr]
#         log.error(sorted(self.keys()))
#         raise AttributeError(attr)
#         #return self.get(attr, None)
#     __setattr__= dict.__setitem__
#     __delattr__= dict.__delitem__
#
#
#     def __copy__(self):
#         return dotdict(self)
#
#     def __deepcopy__(self, memo):
#         new_dict = dotdict()
#         for k, v in self.items():
#             new_dict[k] = copy.deepcopy(v, memo)
#         return new_dict
#
#     # pylint: disable=multiple-statements
#     def __getstate__(self): return self.__dict__
#     def __setstate__(self, d): self.__dict__.update(d)
#
#     def deepConvert(self):
#         '''Convert all dicts at all tree levels into dotdict'''
#         for k, v in self.items():
#             if type(v) is dict: # pylint: disable=unidiomatic-typecheck
#                 self[k] = dotdict(v)
#                 self[k].deepConvert()
#             try: # try enumerable types
#                 for m, x in enumerate(v):
#                     if type(x) is dict: # pylint: disable=unidiomatic-typecheck
#                         x = dotdict(x)
#                         x.deepConvert()
#                         v[m] = x#

#             except TypeError:
#                 pass
#         return self
#
#     def copy(self):
#         # override dict.copy()
#         return dotdict(self)


def prhist(ary, prefix_str=None, **kwargs):
    if prefix_str is None:
        prefix_str = ''
    else:
        prefix_str += ' '

    count_ary, bins_ary = np.histogram(ary, **kwargs)
    for i in range(count_ary.shape[0]):
        print("{}{:-8.2f}".format(prefix_str, bins_ary[i]), "{:-10}".format(count_ary[i]))
    print("{}{:-8.2f}".format(prefix_str, bins_ary[-1]))

# def dumpCuda():
#     # small_count = 0
#     total_bytes = 0
#     size2count_dict = collections.defaultdict(int)
#     size2bytes_dict = {}
#     for obj in gc.get_objects():
#         if isinstance(obj, torch.cuda._CudaBase):
#             nbytes = 4
#             for n in obj.size():
#                 nbytes *= n
#
#             size2count_dict[tuple([obj.get_device()] + list(obj.size()))] += 1
#             size2bytes_dict[tuple([obj.get_device()] + list(obj.size()))] = nbytes
#
#             total_bytes += nbytes
#
#     # print(small_count, "tensors equal to or less than than 16 bytes")
#     for size, count in sorted(size2count_dict.items(), key=lambda sc: (size2bytes_dict[sc[0]] * sc[1], sc[1], sc[0])):
#         print('{:4}x'.format(count), '{:10,}'.format(size2bytes_dict[size]), size)
#     print('{:10,}'.format(total_bytes), "total bytes")


def enumerateWithEstimate(iter, desc_str, start_ndx=0, print_ndx=4, backoff=2, iter_len=None):
    if iter_len is None:
        iter_len = len(iter)

    assert backoff >= 2
    while print_ndx < start_ndx * backoff:
        print_ndx *= backoff

    log.warning("{} ----/{}, starting".format(
        desc_str,
        iter_len,
    ))
    start_ts = time.time()
    for (current_ndx, item) in enumerate(iter):
        yield (current_ndx, item)
        if current_ndx == print_ndx:
            duration_sec = ((time.time() - start_ts)
                            / (current_ndx - start_ndx + 1)
                            * (iter_len-start_ndx)
                            )

            done_dt = datetime.datetime.fromtimestamp(start_ts + duration_sec)
            done_td = datetime.timedelta(seconds=duration_sec)

            log.warning("{} {:-4}/{}, done at {}, {}".format(
                desc_str,
                current_ndx,
                iter_len,
                str(done_dt).rsplit('.', 1)[0],
                str(done_td).rsplit('.', 1)[0],
            ))

            print_ndx *= backoff

        if current_ndx + 1 == start_ndx:
            start_ts = time.time()

    log.warning("{} ----/{}, done at {}".format(
        desc_str,
        iter_len,
        str(datetime.datetime.now()).rsplit('.', 1)[0],
    ))


try:
    import matplotlib
    matplotlib.use('agg', warn=False)

    import matplotlib.pyplot as plt
    # matplotlib color maps
    cdict = {'red':   ((0.0,  1.0, 1.0),
                       # (0.5,  1.0, 1.0),
                       (1.0,  1.0, 1.0)),

             'green': ((0.0,  0.0, 0.0),
                       (0.5,  0.0, 0.0),
                       (1.0,  0.5, 0.5)),

             'blue':  ((0.0,  0.0, 0.0),
                       # (0.5,  0.5, 0.5),
                       # (0.75, 0.0, 0.0),
                       (1.0,  0.0, 0.0)),

             'alpha':  ((0.0, 0.0, 0.0),
                       (0.75, 0.5, 0.5),
                       (1.0,  0.5, 0.5))}

    plt.register_cmap(name='mask', data=cdict)

    cdict = {'red':   ((0.0,  0.0, 0.0),
                       (0.25,  1.0, 1.0),
                       (1.0,  1.0, 1.0)),

             'green': ((0.0,  1.0, 1.0),
                       (0.25,  1.0, 1.0),
                       (0.5, 0.0, 0.0),
                       (1.0,  0.0, 0.0)),

             'blue':  ((0.0,  0.0, 0.0),
                       # (0.5,  0.5, 0.5),
                       # (0.75, 0.0, 0.0),
                       (1.0,  0.0, 0.0)),

             'alpha':  ((0.0, 0.15, 0.15),
                       (0.5,  0.3, 0.3),
                       (0.8,  0.0, 0.0),
                       (1.0,  0.0, 0.0))}

    plt.register_cmap(name='maskinvert', data=cdict)
except ImportError:
    pass
