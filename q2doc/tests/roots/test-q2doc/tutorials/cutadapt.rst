Cutadapt Tutorial
=================

Download and import data used in this tutorial
----------------------------------------------

.. note::
   the `forward.fastq.gz` and `metadata.tsv` files will be stored under
   the `data/` dir, which will be the extent of the data scope. Everything
   stored in `data/` will get download blocks generated automatically.

First, we declare data needed by the usage example that follows. This will render download elements.  At this point,
we don't mention anything driver-specific - just get the data.

.. usage::
   :factory:

   data:
     name: data
     type: MultiplexedSingleEndBarcodeInSequence
     path: forward.fastq.gz

   metadata:
     name: metadata
     path: metadata.tsv


The data here consists of single-end reads (6 reads total). There are two
samples present in the data, with the following barcodes on the 5' end:

.. usage::
    data = use.init_data('data', data)
    metadata = use.init_metadata('metadata', metadata)


Demultiplex the reads
---------------------

Now that we have everything imported, let's do the thing:

.. usage::
  barcodes_col = use.get_metadata_column('barcodes', metadata)

  use.action(
      usage.UsageAction(
          plugin_id='cutadapt',
          action_id='demux_single',
      ),
      usage.UsageInputs(
          seqs=data,
          error_rate=0,
          barcodes=barcodes_col,
      ),
      usage.UsageOutputNames(
          per_sample_sequences='demultiplexed_seqs',
          untrimmed_sequences='untrimmed',
      )
  )

As you can see - the reads are now demuxed. Enjoy!
