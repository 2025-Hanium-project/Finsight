from pathlib import Path

def read_files(security):
    base_dir = Path(__file__).parent.parent
    txt_dir = base_dir / "consensus_to_txt" / security
    txt_list = []
    for txt_file in txt_dir.glob("*.txt"):
        txt_list.append(txt_file)
    return txt_list

if __name__ == "__main__":
    txt_list = read_files("bnk")
    for i in txt_list:
        print(i)
        