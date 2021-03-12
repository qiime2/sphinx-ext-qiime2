"Moving Pictures" tutorial
==========================

.. note:: This guide assumes you have installed QIIME 2 using one of the procedures in the :doc:`install documents <../install/index>`.

.. note:: This guide uses QIIME 2-specific terminology, please see the :doc:`glossary <../glossary>` for more details.

In this tutorial you'll use QIIME 2 to perform an analysis of human microbiome samples from two individuals at four body sites at five timepoints, the first of which immediately followed antibiotic usage. A study based on these samples was originally published in `Caporaso et al. (2011)`_. The data used in this tutorial were sequenced on an Illumina HiSeq using the `Earth Microbiome Project`_ hypervariable region 4 (V4) 16S rRNA sequencing protocol.

.. qiime1-users::
   These are the same data that are used in the QIIME 1 `Illumina Overview Tutorial`_.

Before beginning this tutorial, create a new directory and change to that directory.

.. command-block::
   :no-exec:

   mkdir qiime2-moving-pictures-tutorial
   cd qiime2-moving-pictures-tutorial

Sample metadata
---------------

Before starting the analysis, explore the sample metadata to familiarize yourself with the samples used in this study. The `sample metadata`_ is available as a Google Sheet. You can download this file as tab-separated text by selecting ``File`` > ``Download as`` > ``Tab-separated values``. Alternatively, the following command will download the sample metadata as tab-separated text and save it in the file ``sample-metadata.tsv``. This ``sample-metadata.tsv`` file is used throughout the rest of the tutorial.

.. download::
   :url: https://data.qiime2.org/2021.2/tutorials/moving-pictures/sample_metadata.tsv
   :saveas: sample-metadata.tsv

.. tip:: `Keemei`_ is a Google Sheets add-on for validating sample metadata. Validation of sample metadata is important before beginning any analysis. Try installing Keemei following the instructions on its website, and then validate the sample metadata spreadsheet linked above. The spreadsheet also includes a sheet with some invalid data to try out with Keemei.

.. tip:: To learn more about metadata, including how to format your metadata for use with QIIME 2, check out :doc:`the metadata tutorial <metadata>`.

Obtaining and importing data
----------------------------

Download the sequence reads that we'll use in this analysis. In this tutorial we'll work with a small subset of the complete sequence data so that the commands will run quickly.

.. command-block::

   mkdir emp-single-end-sequences

.. download::
   :url: https://data.qiime2.org/2021.2/tutorials/moving-pictures/emp-single-end-sequences/barcodes.fastq.gz
   :saveas: emp-single-end-sequences/barcodes.fastq.gz

.. download::
   :url: https://data.qiime2.org/2021.2/tutorials/moving-pictures/emp-single-end-sequences/sequences.fastq.gz
   :saveas: emp-single-end-sequences/sequences.fastq.gz

All data that is used as input to QIIME 2 is in form of QIIME 2 artifacts, which contain information about the type of data and the source of the data. So, the first thing we need to do is import these sequence data files into a QIIME 2 artifact.

The semantic type of this QIIME 2 artifact is ``EMPSingleEndSequences``. ``EMPSingleEndSequences`` QIIME 2 artifacts contain sequences that are multiplexed, meaning that the sequences have not yet been assigned to samples (hence the inclusion of both ``sequences.fastq.gz`` and ``barcodes.fastq.gz`` files, where the ``barcodes.fastq.gz`` contains the barcode read associated with each sequence in ``sequences.fastq.gz``.) To learn about how to import sequence data in other formats, see the :doc:`importing data tutorial <importing>`.

.. command-block::

   qiime tools import \
     --type EMPSingleEndSequences \
     --input-path emp-single-end-sequences \
     --output-path emp-single-end-sequences.qza
