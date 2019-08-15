#AUTOGENERATED! DO NOT EDIT! File to edit: dev/06_data_source.ipynb (unless otherwise specified).

__all__ = ['DataSource', 'DsrcSubset', 'DsrcSubset']

from ..imports import *
from ..test import *
from ..core import *
from .core import *
from .transform import *
from .pipeline import *
from ..notebook.showdoc import show_doc

class _FiltTfmdList(TfmdList):
    "Like `TfmdList` but with filters and train/valid attribute, for proper setup"
    def __init__(self, items, tfms, filts, filt_idx, do_setup=True, as_item=True):
        self.filts,self.filt_idx = filts,filt_idx
        super().__init__(items, tfms, do_setup=do_setup, as_item=as_item, filt=None)

    def __getitem__(self, i):
        self.filt = self.filt_idx[i[0] if is_iter(i) else i]
        return self.get(i)

    @property
    def n_subsets(self): return len(self.filts)
    def len(self,filt): return len(self.filts[filt])
    def subset(self, i): return DsrcSubset(self, i)
    def subsets(self): return map(self.subset, range(self.n_subsets))

_FiltTfmdList.train,_FiltTfmdList.valid = add_props(lambda i,x: x.subset(i), 2)

class DataSource(TfmdDS):
    "Applies a `tfm` to filtered subsets of `items`"
    def __init__(self, items, type_tfms=None, ds_tfms=None, filts=None, do_setup=True):
        if filts is None: filts = [range_of(items)]
        self.filts = L(mask2idxs(filt) for filt in filts)
        # Create map from item id to filter id
        assert all_disjoint(self.filts)

        self.items = L(items)
        self.filt_idx = L([None]*len(self.items))
        for i,f in enumerate(self.filts): self.filt_idx[f] = i

        self.tls = [_FiltTfmdList(self.items, t, self.filts, self.filt_idx, do_setup=do_setup)
                    for t in L(type_tfms)]
        self._mk_pipeline(ds_tfms, do_setup=do_setup, as_item=False, filt=None)

    @property
    def n_subsets(self): return len(self.filts)
    def len(self,filt): return len(self.filts[filt])
    def subset(self, i): return DsrcSubset(self, i)
    def subsets(self): return map(self.subset, range(self.n_subsets))
    def __repr__(self):
        return '\n'.join(map(str,self.subsets())) + f'\ntls - {self.tls}\nds tfms - {self.tfms}'

    def __getitem__(self, i):
        self.filt = self.filt_idx[i[0] if is_iter(i) else i]
        return self.get(i)

    def databunch(self, tfms=None, bs=16, val_bs=None, shuffle_train=True,
                  sampler=None, batch_sampler=None,  **kwargs):
        n = self.n_subsets-1
        bss = [bs] + [2*bs]*n if val_bs is None else [bs] + [val_bs]*n
        shuffles = [shuffle_train] + [False]*n
        dls = [TfmdDL(self.subset(i), tfms, b, shuffle=s, drop_last=s, sampler=sa, batch_sampler=bsa, **kwargs)
               for i,(b,s,sa,bsa) in enumerate(zip(bss, shuffles, L(sampler).cycle(), L(batch_sampler).cycle()))]
        return DataBunch(*dls)

DataSource.train,DataSource.valid = add_props(lambda i,x: x.subset(i), 2)

@docs
class DsrcSubset():
    "A filtered subset of a `DataSource`"
    def __init__(self, dsrc, filt):
        self.dsrc,self.filt,self.filts = dsrc,filt,dsrc.filts[filt]
        self.tfms,self.type_tfms,self.ds_tfms = map(lambda x: getattr(dsrc, x, None), ['tfms', 'type_tfms', 'ds_tfms'])

    def __getitem__(self,i):             return self.dsrc[self.filts[i]]
    def decode(self, o, **kwargs):       return self.dsrc.decode(o, **kwargs)
    def decode_batch(self, b, **kwargs): return self.dsrc.decode_batch(b, **kwargs)
    def decode_at(self, i, **kwargs):    return self.decode(self[i], **kwargs)
    def show     (self, o, **kwargs):    return self.dsrc.show(o, filt=self.filt, **kwargs)
    def show_at  (self, i, **kwargs):    return self.dsrc.show(self[i], filt=self.filt, **kwargs)
    def __len__(self):  return len(self.filts)
    def __iter__(self): return (self[i] for i in range_of(self.filts))
    def __eq__(self,b): return all_equal(b,self)
    def __repr__(self): return coll_repr(self)

    @property
    def items(self): return L(self.dsrc.items[i] for i in self.filts)

    _docs = dict(decode="Transform decode",
                 show="Transform show",
                 decode_batch="Transform decode batch",
                 __getitem__="Encoded item(s) at `i`",
                 decode_at="Decoded item at `i`",
                 show_at="Show decoded item at `i`")

class DsrcSubset(TfmdDS):
    "A filtered subset of a `DataSource`"
    def __init__(self, dsrc, filt):
        items = dsrc.items[dsrc.filts[filt]]
        type_tfms = [o.tfms for o in dsrc.tls]
        super().__init__(items, type_tfms=type_tfms, ds_tfms=dsrc.tfms, do_setup=False, filt=filt)

    def __repr__(self): return coll_repr(self)