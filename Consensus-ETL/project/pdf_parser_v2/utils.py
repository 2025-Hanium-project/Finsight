from pathlib import Path

def read_files(security):
    # 현재 파일의 경로 기준 상대 경로 : project/
    base_dir = Path(__file__).parent.parent 
    # project/consensus_to_txt / ....
    txt_dir = base_dir / "consensus_to_txt" / security 
    txt_list = []
    for txt_file in txt_dir.glob("*.txt"):
        txt_list.append(txt_file)
    # read_files 함수가 반환하는 것은 Path 객체 리스트. 따라서 path를 포함한 파일명을 리턴함
    return txt_list

def extract_all_info(txt_files):
    """
    각 txt 파일에서 첫 줄(혹은 원하는 정보)을 추출하여 리스트로 반환
    """
    info_list = []
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                first_line = f.read().strip()
                info_list.append({'file': txt_file.name, 'info': first_line})
        except Exception as e:
            print(f"{txt_file.name} 읽기 실패: {e}")
            info_list.append({'file': txt_file.name, 'info': ''})
    return info_list
