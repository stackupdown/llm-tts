# . ./set_proxy.sh
# torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 3.74 GiB.
# GPU 0 has a total capacity of 4.00 GiB of which 0 bytes is free.
# Including non-PyTorch memory, this process has 17179869184.00 GiB memory in use.
# Process 74390 has 17179869184.00 GiB memory in use. Of the allocated memory 16.20 GiB is allocated by PyTorch,
# and 844.14 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting
# PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.
#  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)
# action = remove speaker + output to sound + merge files + inference

# TEXT=data/hamlet/hamlet_merge.txt
TEXT=tools/harry_porter_merge.txt
python inference_am_vocoder_joint.py \
--logdir prompt_tts_open_source_joint \
--config_folder config/joint \
--checkpoint g_00140000 \
--test_file $TEXT \
--sub_dir harry
