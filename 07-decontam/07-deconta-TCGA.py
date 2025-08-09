import os
import subprocess
import argparse
from multiprocessing import Pool
import gzip

def print_colorful_message(message, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
    }
    end_color = '\033[0m'
    if color not in colors:
        print("Invalid color. Please choose from 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'.")
        return
    colored_message = f"{colors[color]}{message}{end_color}"
    print(colored_message)

def compress_to_gz(file_path):
    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as f_in:
            with gzip.open(file_path + '.gz', 'wb') as f_out:
                f_out.writelines(f_in)
        os.remove(file_path)
    else:
        print(f"File {file_path} not found or invalid. Compression skipped.")

def rmc_extract_microbiome_reads(sample_info, is_single_end=False, itm_path=None):
    sample_id, fastq_r1, kraken_output, output_r1, output_r3, output_r4, path4_ku1, path6_rcr = sample_info
    report_file = os.path.join(path4_ku1, f"{sample_id}_.kraken.report.txt")
    task_complete_file = os.path.join(path6_rcr, f"{sample_id}.task.complete")

    if os.path.exists(report_file) and os.path.exists(task_complete_file):
        print(f">>> Sample {sample_id} already processed. Skipping...")
        return

    conta_file = os.path.join(itm_path, "itm_helper", "conta_list.txt")
    with open(conta_file, "r") as file:
        lines = file.readlines()
    second_column = [line.strip().split()[1] for line in lines if len(line.strip().split()) > 1]
    conta_ls = [taxid for taxid in second_column if taxid.isdigit()]

    print_colorful_message(f">>> Running decontamination process for sample {sample_id}...", "cyan")

    if is_single_end:
        process_args = ["python", os.path.join(itm_path, "itm_helper", "extract_kraken_reads.py"),
                        "-k", kraken_output, "-U", fastq_r1, "-o", output_r1,
                        "--taxid", *conta_ls, "--exclude", "--include-children", "-r", report_file]
    else:
        fastq_r2 = fastq_r1.replace("_mr_1.fastq", "_mr_2.fastq")
        process_args = ["python", os.path.join(itm_path, "itm_helper", "extract_kraken_reads.py"),
                        "-k", kraken_output, "-s1", fastq_r1, "-s2", fastq_r2, "-o", output_r3, "-o2", output_r4,
                        "--taxid", *conta_ls, 
                        "--exclude", "--include-children", "-r", report_file]

    process_args = [arg for arg in process_args if arg is not None]

    print(f"Running command: {' '.join(process_args)}")

    process = subprocess.Popen(process_args)
    process.wait()
    if process.returncode == 0:
        with open(task_complete_file, "w") as f:
            f.write("Task completed.")
        print(f">>>--- Sample {sample_id} processed successfully.")
        print("   ")

        if is_single_end:
            compress_to_gz(output_r1)
        else:
            compress_to_gz(output_r3)
            compress_to_gz(output_r4)
    else:
        print(f"Error occurred while processing sample {sample_id}.")

def step5_decontamination(path5_mr, path4_ku1, path6_rcr, itm_path, batch_size=1, is_single_end=False):
    print("   ")
    print_colorful_message("#########################################################", "blue")
    print_colorful_message(" ITMtools: Identifing Intratumoral Microbiome pipeline ", "cyan")
    print_colorful_message(" If you encounter any issues, please report them at ", "cyan")
    print_colorful_message(" https://github.com/LiaoWJLab/ITMtools/issues ", "cyan")
    print_colorful_message("#########################################################", "blue")
    print(" Author: Dongqiang Zeng, Qianqian Mao ")
    print(" Email: interlaken@smu.edu.cn ")
    print_colorful_message("#########################################################", "blue")
    print("   ")

    print("  Extracting microbiome reads using extract_kraken_reads.py from KrakenTools:")
    print("  https://github.com/jenniferlu717/KrakenTools")

    print("   ")
    print("   ")

    os.makedirs(path6_rcr, exist_ok=True)

    if is_single_end:
        fastq_files = [file for file in os.listdir(path5_mr) if file.endswith("_mr.fastq")]
    else:
        fastq_files = [file for file in os.listdir(path5_mr) if file.endswith("_mr_1.fastq")]

    print(f"Found {len(fastq_files)} FASTQ files to process.")

    if not fastq_files:
        print("No FASTQ files found. Please check the input directory and file naming conventions.")
        return

    samples = []
    for fastq_r1 in fastq_files:
        if is_single_end:
            sample_id = fastq_r1.replace("_mr.fastq", "")
            fastq_r1_path = os.path.join(path5_mr, f"{sample_id}_mr.fastq")
            samples.append((sample_id, fastq_r1_path, os.path.join(path4_ku1, f"{sample_id}_.kraken.output.txt"),
                            os.path.join(path6_rcr, f"{sample_id}_rcr.fastq"), None, None, path4_ku1, path6_rcr))
        else:
            sample_id = fastq_r1.replace("_mr_1.fastq", "")
            fastq_r1_path = os.path.join(path5_mr, f"{sample_id}_mr_1.fastq")
            fastq_r2_path = os.path.join(path5_mr, f"{sample_id}_mr_2.fastq")
            samples.append((sample_id, fastq_r1_path, os.path.join(path4_ku1, f"{sample_id}_.kraken.output.txt"), None, 
                            os.path.join(path6_rcr, f"{sample_id}_rcr_1.fastq"), os.path.join(path6_rcr, f"{sample_id}_rcr_2.fastq"), 
                            path4_ku1, path6_rcr))

    print(f"Processing {len(samples)} samples in batches of {batch_size}.")

    with Pool() as pool:
        for i in range(0, len(samples), batch_size):
            batch = samples[i:i + batch_size]
            if is_single_end:
                pool.starmap(rmc_extract_microbiome_reads, [(sample, is_single_end, itm_path) for sample in batch])
            else:
                pool.starmap(rmc_extract_microbiome_reads, [(sample, is_single_end, itm_path) for sample in batch])
    print("   ")
    print(">>>=== Microbiome reads extraction completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 5: Decontaminate microbiome reads from Kraken2 output")
    parser.add_argument("--path5_mr", type=str, help="Path to extracted microbiome reads")
    parser.add_argument("--path4_ku1", type=str, help="Path to Kraken2 outputs")
    parser.add_argument("--path6_rcr", type=str, help="Path to decontaminate microbiome reads")
    parser.add_argument("--itm_path", type=str, help="Path to ITMtools")
    parser.add_argument("--batch_size", type=int, default=1, help="Number of samples to process simultaneously")
    parser.add_argument("--se", action="store_true", help="Use single-end processing. Default is paired-end.")
    args = parser.parse_args()

    step5_decontamination(args.path5_mr, args.path4_ku1, args.path6_rcr, args.itm_path, args.batch_size, args.se)
