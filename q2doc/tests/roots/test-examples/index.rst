Factories
=========

Ints
----

.. q2:usage::
   :factory: data
   :name: ints_a

   def ints1_factory():
       from qiime2.core.testing.type import IntSequence1
       return Artifact.import_data(IntSequence1, [0, 1, 2])

.. q2:usage::
   :factory: data
   :name: ints_b

   def ints2_factory():
       from qiime2.core.testing.type import IntSequence1
       return Artifact.import_data(IntSequence1, [3, 4, 5])

.. q2:usage::
   :factory: data
   :name: ints_c

   def ints3_factory():
       from qiime2.core.testing.type import IntSequence2
       return Artifact.import_data(IntSequence2, [6, 7, 8])

.. q2:usage::
   :factory: data
   :name: single_int1

   def single_int1_factory():
       from qiime2.core.testing.type import SingleInt
       return Artifact.import_data(SingleInt, 10)

.. q2:usage::
   :factory: data
   :name: single_int2

   def single_int2_factory():
       from qiime2.core.testing.type import SingleInt
       return Artifact.import_data(SingleInt, 11)

Mapping
--------

.. q2:usage::
   :factory: data
   :name: mapper

   def mapping1_factory():
       from qiime2.core.testing.type import Mapping
       return Artifact.import_data(Mapping, {'a': 42})

Metadata
---------

.. q2:usage::
   :factory: metadata
   :name: md1

   def md1_factory():
       return Metadata(pd.DataFrame({'a': ['1', '2', '3']},
                                   index=pd.Index(['0', '1', '2'],
                                                   name='id')))

.. q2:usage::
   :factory: metadata
   :name: md2

   def md2_factory():
       return Metadata(pd.DataFrame({'b': ['4', '5', '6']},
                                   index=pd.Index(['0', '1', '2'],
                                                   name='id')))


Basic Usage
===========

.. q2:usage::
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

Chained Usage
===============
.. q2:usage::

   use.comment('This example demonstrates chained usage (pt 1).')
   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='concatenate_ints'),
       use.UsageInputs(ints1=ints_a, ints2=ints_b, ints3=ints_c, int1=4,
                       int2=2),
       use.UsageOutputNames(concatenated_ints='ints_d'),
   )

   ints_d = use.get_result('ints_d')
   use.comment('This example demonstrates chained usage (pt 2).')
   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='concatenate_ints'),
       use.UsageInputs(ints1=ints_d, ints2=ints_b, ints3=ints_c, int1=41,
                       int2=0),
       use.UsageOutputNames(concatenated_ints='concatenated_ints'),
   )


Simple Pipeline
================

.. q2:usage::
   mapper = use.init_data('mapper', mapping1_factory)

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='typical_pipeline'),
       use.UsageInputs(int_sequence=ints_a, mapping=mapper,
                       do_extra_thing=True),
       use.UsageOutputNames(out_map='out_map', left='left', right='right',
                            left_viz='left_viz', right_viz='right_viz')
   )


Complex Pipeline
================

.. q2:usage::

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='typical_pipeline'),
       use.UsageInputs(int_sequence=ints_a, mapping=mapper,
                       do_extra_thing=True),
       use.UsageOutputNames(out_map='out_map1', left='left1', right='right1',
                            left_viz='left_viz1', right_viz='right_viz1')
   )

   ints2 = use.get_result('left1')
   mapper2 = use.get_result('out_map1')

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='typical_pipeline'),
       use.UsageInputs(int_sequence=ints2, mapping=mapper2,
                       do_extra_thing=False),
       use.UsageOutputNames(out_map='out_map2', left='left2', right='right2',
                            left_viz='left_viz2', right_viz='right_viz2')
   )

   right2 = use.get_result('right2')
   right2.assert_has_line_matching(
       label='a nice label about this assertion',
       path='ints.txt',
       expression='1',
   )


Identity with Metadata Simple
=============================

.. q2:usage::

   md1 = use.init_metadata('md1', md1_factory)

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='identity_with_metadata'),
       use.UsageInputs(ints=ints_a, metadata=md1),
       use.UsageOutputNames(out='out'),
   )


Identity with Metadata Merging
==============================

.. q2:usage::

   md2 = use.init_metadata('md2', md2_factory)
   md3 = use.merge_metadata('md3', md1, md2)

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='identity_with_metadata'),
       use.UsageInputs(ints=ints_a, metadata=md3),
       use.UsageOutputNames(out='out2'),
   )


Identity With Metadata Column Get MDC
=====================================

.. q2:usage::

   mdc = use.get_metadata_column('a', md1)

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='identity_with_metadata_column'),
       use.UsageInputs(ints=ints_a, metadata=mdc),
       use.UsageOutputNames(out='out3'),
   )


Variadic Input Simple
=====================

.. q2:usage::

   int_collection = use.init_data_collection('int_collection', list, ints_a, ints_b)

   single_int1 = use.init_data('single_int1', single_int1_factory)
   single_int2 = use.init_data('single_int2', single_int2_factory)
   int_set = use.init_data_collection('int_set', set, single_int1,
                                      single_int2)

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='variadic_input_method'),
       use.UsageInputs(ints=int_collection, int_set=int_set, nums={7, 8, 9}),
       use.UsageOutputNames(output='out4'),
   )



Optional Inputs
===============

.. q2:usage::

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='optional_artifacts_method'),
       use.UsageInputs(ints=ints_a, num1=1),
       use.UsageOutputNames(output='output5'),
   )

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='optional_artifacts_method'),
       use.UsageInputs(ints=ints_a, num1=1, num2=2),
       use.UsageOutputNames(output='output6'),
   )

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='optional_artifacts_method'),
       use.UsageInputs(ints=ints_a, num1=1, num2=None),
       use.UsageOutputNames(output='ints_b'),
   )

   optional1 = use.get_result('ints_b')

   use.action(
       use.UsageAction(plugin_id='dummy_plugin',
                       action_id='optional_artifacts_method'),
       use.UsageInputs(ints=ints_a, optional1=optional1, num1=3, num2=4),
       use.UsageOutputNames(output='output7'),
   )
