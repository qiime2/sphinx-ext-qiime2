Factories
=========

Ints
----

.. usage::
   :factory: data
   :name: ints_a

   def ints1_factory():
       from qiime2.core.testing.type import IntSequence1
       return Artifact.import_data(IntSequence1, [0, 1, 2])

.. usage::
   :factory: data
   :name: ints_b

   def ints2_factory():
       from qiime2.core.testing.type import IntSequence1
       return Artifact.import_data(IntSequence1, [3, 4, 5])

.. usage::
   :factory: data
   :name: ints_c

   def ints3_factory():
       from qiime2.core.testing.type import IntSequence2
       return Artifact.import_data(IntSequence2, [6, 7, 8])

.. usage::
   :factory: metadata
   :name: int1

   def single_int1_factory():
       from qiime2.core.testing.type import SingleInt
       return Artifact.import_data(SingleInt, 10)

.. usage::
   :factory: data
   :name: int2

   def single_int2_factory():
       from qiime2.core.testing.type import SingleInt
       return Artifact.import_data(SingleInt, 11)

Mapping
--------

.. usage::
   :factory: data
   :name: mapping1_factory

   def mapping1_factory():
       from qiime2.core.testing.type import Mapping
       return Artifact.import_data(Mapping, {'a': 42})

Metadata
---------

.. usage::
   :factory: metadata
   :name: md1_factory

   def md1_factory():
       return Metadata(pd.DataFrame({'a': ['1', '2', '3']},
                                   index=pd.Index(['0', '1', '2'],
                                                   name='id')))

.. usage::
   :factory: metadata
   :name: md2_factory

   def md2_factory():
       return Metadata(pd.DataFrame({'b': ['4', '5', '6']},
                                   index=pd.Index(['0', '1', '2'],
                                                   name='id')))


Basic Usage
===========

.. usage::
   ints_a = use.init_data('ints_a', ints1_factory)
   ints_b = use.init_data('ints_b', ints2_factory)
   ints_c = use.init_data('ints_c', ints3_factory)

   use.comment('This example demonstrates basic usage.')
   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='concatenate_ints'),
       use.UsageInputs(ints1=ints_a, ints2=ints_b, ints3=ints_c, int1=4,
                       int2=2),
       use.UsageOutputNames(concatenated_ints='ints_d'),
   )
