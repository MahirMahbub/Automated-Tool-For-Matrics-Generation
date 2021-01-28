# import os
# import subprocess
# #
# # output = subprocess.check_output("und create -languages python E:/repo/PyGithub/v1.43.5/PyGithub-PyGithub-c5499a3",
# #                                  shell=True)
# # output2 = subprocess.check_output(
# #     "und add -db E:/repo/PyGithub/v1.43.5/PyGithub-PyGithub-c5499a3.und "
# #     "E:/repo/PyGithub/v1.43.5/PyGithub-PyGithub-c5499a3",
# #     shell=True)
# # output3 = subprocess.check_output("und analyze -db E:/repo/PyGithub/v1.43.5/PyGithub-PyGithub-c5499a3.und",
# shell=True)
# with os.add_dll_directory("C:/Program Files/SciTools/bin/pc-win64"):
#     import understand
#
#     print(understand.version())
#     db = understand.open(r"E:/repo/PyGithub/v1.43.6/PyGithub-PyGithub-954455c.und")
#     metrics = db.metric(db.metrics())
#     for k, v in sorted(metrics.items()):
#         print(k, "=", v)
#

import os
import subprocess
import zipfile



def generate_report(save_path: str, zip_path: str):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(save_path)

    output = subprocess.check_output("und create -languages python " + str(save_path),
                                     shell=True)
    output2 = subprocess.check_output(
        "und add -db " + str(save_path) + ".und " + str(save_path),
        shell=True)
    output3 = subprocess.check_output("und analyze -db " + str(save_path) + ".und",
                                      shell=True)
    with os.add_dll_directory("C:/Program Files/SciTools/bin/pc-win64"):
        import understand

        print(understand.version())
        db = understand.open(str(save_path) + ".und")
        metrics = db.metric(db.metrics())
        for k, v in sorted(metrics.items()):
            print(k, "=", v)


zip_path=r"E:\repo\PyGithub\v1.50.tar.gz"
save_path=r"D:\GithubReleaseDownload\temp"
generate_report(save_path=save_path, zip_path=zip_path)
