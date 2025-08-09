import os
import subprocess
import argparse

def process_reads(sample_info, itm_path):
    sample_id, fastq_r1, fastq_r2, kraken_output, output_r3, output_r4, report_file = sample_info

    conta_file = os.path.join(itm_path, "itm_helper", "conta_ls-1.txt")
    
    with open(conta_file, "r") as file:
        lines = file.readlines()

    valid_taxids = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) > 1:
            for part in parts:
                if part.isdigit():
                    valid_taxids.append(part)

    print(f"Valid TaxIDs: {valid_taxids}")

    process = subprocess.Popen([
        "python", os.path.join(itm_path, "itm_helper", "extract_kraken_reads.py"),
        "-k", kraken_output, "-s1", fastq_r1, "-s2", fastq_r2, "-o", output_r3, "-o2", output_r4,
        "--taxid", *valid_taxids, "--exclude", "--include-children", "-r", report_file
    ])
    process.wait()

def main(path5_mr, path4_ku1, path6_rcr, itm_path):
    samples = []
    for file in os.listdir(path5_mr):
        if file.endswith("_mr_1.fastq"):
            sample_id = file.replace("_mr_1.fastq", "")
            fastq_r1 = os.path.join(path5_mr, file)
            fastq_r2 = fastq_r1.replace("_mr_1.fastq", "_mr_2.fastq")
            kraken_output = os.path.join(path4_ku1, f"{sample_id}_.kraken.output.txt")
            output_r3 = os.path.join(path6_rcr, f"{sample_id}_rcr_1.fastq")
            output_r4 = os.path.join(path6_rcr, f"{sample_id}_rcr_2.fastq")
            report_file = os.path.join(path4_ku1, f"{sample_id}_.kraken.report.txt")
            sample_info = (sample_id, fastq_r1, fastq_r2, kraken_output, output_r3, output_r4, report_file)
            samples.append(sample_info)

    for sample_info in samples:
        process_reads(sample_info, itm_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 5: Decontaminate microbiome reads from Kraken2 output")
    parser.add_argument("--path5_mr", type=str, required=True, help="Path to extracted microbiome reads")
    parser.add_argument("--path4_ku1", type=str, required=True, help="Path to Kraken2 outputs")
    parser.add_argument("--path6_rcr", type=str, required=True, help="Path to decontaminate microbiome reads")
    parser.add_argument("--itm_path", type=str, required=True, help="Path to ITMtools")
    args = parser.parse_args()

    main(args.path5_mr, args.path4_ku1, args.path6_rcr, args.itm_path)
