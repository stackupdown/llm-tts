if [ ! -d "../data/hamlet" ]; then
    mkdir -p ../data/hamlet
fi

# python merge_file.py -f1 ./hamlet_split.txt -f2 ./data/hamlet_sp_ph.txt -o ./data/hamlet/hamlet_merge.txt

python merge_file.py -f1 ../hamlet_split.txt -o ../data/hamlet/hamlet_merge.txt
