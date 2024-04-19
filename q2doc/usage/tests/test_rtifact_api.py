import tempfile
import textwrap
import unittest

from qiime2.core.testing.util import get_dummy_plugin

from q2doc.usage.driver import RtifactAPIUsage


class TestRtifactAPIUsage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.TemporaryDirectory(prefix='qiime2-test-temp-')
        cls.plugin = get_dummy_plugin()

    @classmethod
    def tearDownClass(cls):
        cls.test_dir.cleanup()

    def test_basic(self):
        action = self.plugin.actions['concatenate_ints']
        use = RtifactAPIUsage()
        action.examples['concatenate_ints_simple'](use)

        exp = """\
        library(reticulate)

        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        # This example demonstrates basic usage.
        action_results <- dummy_plugin_actions$concatenate_ints(
            ints1=ints_a,
            ints2=ints_b,
            ints3=ints_c,
            int1=4L,
            int2=2L,
        )
        ints_d <- action_results$concatenated_ints"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())

    def test_chained(self):
        action = self.plugin.actions['concatenate_ints']
        use = RtifactAPIUsage()
        action.examples['concatenate_ints_complex'](use)

        exp = """\
        library(reticulate)

        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        # This example demonstrates chained usage (pt 1).
        action_results <- dummy_plugin_actions$concatenate_ints(
            ints1=ints_a,
            ints2=ints_b,
            ints3=ints_c,
            int1=4L,
            int2=2L,
        )
        ints_d <- action_results$concatenated_ints
        # This example demonstrates chained usage (pt 2).
        action_results <- dummy_plugin_actions$concatenate_ints(
            ints1=ints_d,
            ints2=ints_b,
            ints3=ints_c,
            int1=41L,
            int2=0L,
        )
        concatenated_ints <- action_results$concatenated_ints"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())

    def test_dereferencing(self):
        action = self.plugin.actions['typical_pipeline']
        use = RtifactAPIUsage()
        action.examples['typical_pipeline_simple'](use)

        exp = """\
        library(reticulate)

        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        action_results <- dummy_plugin_actions$typical_pipeline(
            int_sequence=ints,
            mapping=mapper,
            do_extra_thing=TRUE,
        )
        out_map <- action_results$out_map
        left <- action_results$left
        right <- action_results$right
        left_viz_viz <- action_results$left_viz
        right_viz_viz <- action_results$right_viz"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())

    def test_chained_dereferencing(self):
        action = self.plugin.actions['typical_pipeline']
        use = RtifactAPIUsage()
        action.examples['typical_pipeline_complex'](use)

        exp = """\
        library(reticulate)

        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        action_results <- dummy_plugin_actions$typical_pipeline(
            int_sequence=ints1,
            mapping=mapper1,
            do_extra_thing=TRUE,
        )
        out_map1 <- action_results$out_map
        left1 <- action_results$left
        right1 <- action_results$right
        left_viz1_viz <- action_results$left_viz
        right_viz1_viz <- action_results$right_viz
        action_results <- dummy_plugin_actions$typical_pipeline(
            int_sequence=left1,
            mapping=out_map1,
            do_extra_thing=FALSE,
        )
        out_map2 <- action_results$out_map
        left2 <- action_results$left
        right2 <- action_results$right
        left_viz2_viz <- action_results$left_viz
        right_viz2_viz <- action_results$right_viz"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())

    def test_metadata_merging(self):
        action = self.plugin.actions['identity_with_metadata']
        use = RtifactAPIUsage()
        action.examples['identity_with_metadata_merging'](use)

        exp = """\
        library(reticulate)

        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        md3_md <- md1_md$merge(md2_md)
        action_results <- dummy_plugin_actions$identity_with_metadata(
            ints=ints,
            metadata=md3_md,
        )
        out <- action_results$out"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())

    def test_metadata_column_from_helper(self):
        action = self.plugin.actions['identity_with_metadata_column']
        use = RtifactAPIUsage()
        action.examples['identity_with_metadata_column_get_mdc'](use)

        exp = """\
        library(reticulate)

        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        mdc_mdc <- md_md$get_column('a')
        action_results <- dummy_plugin_actions$identity_with_metadata_column(
            ints=ints,
            metadata=mdc_mdc,
        )
        out <- action_results$out"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())

    def test_optional_inputs(self):
        action = self.plugin.actions['optional_artifacts_method']
        use = RtifactAPIUsage()
        action.examples['optional_inputs'](use)

        exp = """\
        library(reticulate)

        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        action_results <- dummy_plugin_actions$optional_artifacts_method(
            ints=ints,
            num1=1L,
        )
        output1 <- action_results$output
        action_results <- dummy_plugin_actions$optional_artifacts_method(
            ints=ints,
            num1=1L,
            num2=2L,
        )
        output2 <- action_results$output
        action_results <- dummy_plugin_actions$optional_artifacts_method(
            ints=ints,
            num1=1L,
            num2=NULL,
        )
        output3 <- action_results$output
        action_results <- dummy_plugin_actions$optional_artifacts_method(
            ints=ints,
            optional1=output3,
            num1=3L,
            num2=4L,
        )
        output4 <- action_results$output"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())

    def test_artifact_collection_dict_of_ints(self):
        action = self.plugin.actions['dict_of_ints']
        use = RtifactAPIUsage()
        action.examples['collection_dict_of_ints'](use)

        exp = """\
        library(reticulate)

        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        action_results <- dummy_plugin_actions$dict_of_ints(
            ints=ints_artifact_collection,
        )
        out_artifact_collection <- action_results$output"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())

    def test_construct_and_access_collection(self):
        action = self.plugin.actions['dict_of_ints']
        use = RtifactAPIUsage()
        action.examples['construct_and_access_collection'](use)

        exp = """\
        library(reticulate)

        ResultCollection <- import("qiime2")$ResultCollection
        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        rc_in_artifact_collection = ResultCollection(dict(
            'a' = ints_a,
            'b' = ints_b
        ))
        action_results <- dummy_plugin_actions$dict_of_ints(
            ints=rc_in_artifact_collection,
        )
        rc_out_artifact_collection <- action_results$output
        ints_b_from_collection <- rc_out_artifact_collection['b']"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())

    def test_template_collection(self):
        use = RtifactAPIUsage()

        set_input = {1, 3.0, None, 'a'}
        exp = use.INDENT + "input=builtins$set(list(1L, 3.0, NULL, 'a')),"
        obs = use._template_input('input', set_input)
        self.assertEqual(exp, obs)

        list_input = [1, 3.0]
        exp = use.INDENT + "input=list(1L, 3.0),"
        obs = use._template_input('input', list_input)
        self.assertEqual(exp, obs)

        list_input_bool = [False, True]
        exp = use.INDENT + "input=list(FALSE, TRUE),"
        obs = use._template_input('input', list_input_bool)
        self.assertEqual(exp, obs)

    def test_builtins_import(self):
        action = self.plugin.actions['variadic_input_method']
        use = RtifactAPIUsage()
        action.examples['variadic_input_simple'](use)

        exp = """\
        library(reticulate)

        builtins <- import_builtins()
        dummy_plugin_actions <- import("qiime2.plugins.dummy_plugin.actions")

        action_results <- dummy_plugin_actions$variadic_input_method(
            ints=list(ints_a, ints_b),
            int_set=builtins$set(list(single_int1, single_int2)),
            nums=builtins$set(list(7L, 8L, 9L)),
        )
        out <- action_results$output"""
        exp = textwrap.dedent(exp)

        self.assertEqual(exp, use.render())
