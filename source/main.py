# from source import GithubReleaseDownloader
import multiprocessing
import os
import shutil
import subprocess
import threading
import zipfile
from collections import defaultdict
from os.path import join
from threading import Thread
from typing import Optional, List

import pandas as pd
import requests
from github import Github
from github.GitRelease import GitRelease
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from pydantic import HttpUrl
from requests import Response



# from metric_generator import generate_report


class GithubReleaseDownloader(object):

    def __init__(self, user_name: Optional[str] = None, password: Optional[str] = None,
                 access_token: Optional[str] = None):
        self._user_name: str = user_name
        self._password: str = password
        self._access_token: str = access_token


    @staticmethod
    def download_url(url: HttpUrl, save_path: Optional[str] = os.getcwd(), chunk_size: Optional[int] = 64):
        r: Response = requests.get(url, stream=True)
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)


    def _create_new_download_thread(self, url: str, save_path: str, chunk_size: int):
        download_thread: Thread = threading.Thread(target=self.download_url, args=(url, save_path, chunk_size))
        download_thread.start()
        return download_thread


    def download_tags(self, repository: str,
                      save_path: Optional[str] = os.getcwd(), thread_number: Optional[int] = 5):
        if thread_number > 128:
            assert "Number of Thread is too high"
        _cred: Github = self._authenticate_to_github(self._access_token, self._password, self._user_name)
        _repo: Repository = _cred.get_repo(repository)
        _repo_name: str = self._get_repository_name(repository)
        _releases = _repo.get_tags()
        for i in _releases:
            print(i.zipball_url)

        _download_links: List[str] = self._get_release_zipball_urls(_releases)
        _number_of_release: int = len(_download_links)
        for start_index in range(0, _number_of_release, thread_number):
            _last_index: int
            _thread_list: List[Thread]
            _last_index, _thread_list = self._calculate_last_index_for_threading(_number_of_release, start_index,
                                                                                 thread_number)
            for ref in _download_links[start_index:_last_index]:
                print("Downloading.....: ", ref)
                _version_name: str = self._get_release_version(ref)
                self._check_and_create_local_repo_dir(_repo_name, save_path)
                _thread_list.append(
                    self._create_new_download_thread(url=ref,
                                                     save_path=save_path + "\\" + _repo_name + "\\" + _version_name +
                                                               ".zip",
                                                     chunk_size=320 // _number_of_release))
            for thread in _thread_list:
                thread.join()


    def download_releases(self, repository: str,
                          save_path: Optional[str] = os.getcwd(), thread_number: Optional[int] = 5):
        if thread_number > 128:
            assert "Number of Thread is too high"
        _cred: Github = self._authenticate_to_github(self._access_token, self._password, self._user_name)
        _repo: Repository = _cred.get_repo(repository)
        _repo_name: str = self._get_repository_name(repository)
        _releases: PaginatedList[GitRelease] = _repo.get_releases()
        for i in _releases:
            print(i.zipball_url)
        _download_links: List[str] = self._get_release_zipball_urls(_releases)
        _number_of_release: int = len(_download_links)
        for start_index in range(0, _number_of_release, thread_number):
            _last_index: int
            _thread_list: List[Thread]
            _last_index, _thread_list = self._calculate_last_index_for_threading(_number_of_release, start_index,
                                                                                 thread_number)
            for ref in _download_links[start_index:_last_index]:
                print("Downloading.....: ", ref)
                _version_name: str = self._get_release_version(ref)
                self._check_and_create_local_repo_dir(_repo_name, save_path)
                _thread_list.append(
                    self._create_new_download_thread(url=ref,
                                                     save_path=save_path + "\\" + _repo_name + "\\" + _version_name +
                                                               ".zip",
                                                     chunk_size=320 // _number_of_release))
            for thread in _thread_list:
                thread.join()


    @staticmethod
    def _check_and_create_local_repo_dir(repo_name: str, save_path: str):
        if not os.path.exists(save_path + "\\" + repo_name):
            os.makedirs(save_path + "\\" + repo_name)


    @staticmethod
    def _get_release_version(ref: str):
        version_name: str = ref.split("/")[-1]
        return version_name


    @staticmethod
    def _calculate_last_index_for_threading(number_of_release: int, start_index: int, thread_number: int):
        last_index: int = start_index + thread_number
        if last_index > number_of_release:
            last_index = number_of_release
        thread_list: List[Thread] = []
        return last_index, thread_list


    @staticmethod
    def _get_repository_name(repository: str):
        repo_name: str = repository.split('/')[-1]
        return repo_name


    @staticmethod
    def _get_release_zipball_urls(releases: PaginatedList):
        download_links: List[str] = []
        for release in releases:
            download_links.append(release.zipball_url)
        return download_links


    @staticmethod
    def _authenticate_to_github(access_token: str, password: str, user_name: str):
        if access_token is None:
            cred: Github = Github(user_name, password)
        else:
            cred: Github = Github(access_token)
        return cred



class MetricsGenerator(object):

    def __init__(self, source_folder):
        self.source_folder: str = source_folder


    def unzip_all(self, save_path: str):
        zip_files = [join(self.source_folder, f) for f in os.listdir(self.source_folder) if f.endswith('.zip')]
        args = []
        for zip_path in zip_files:
            file_name = os.path.basename(zip_path)[:-4]
            args.append((file_name, save_path, zip_path))
        jobs = []
        pool_size = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=pool_size)
        pool_outputs = pool.starmap(self.unzip_multiprocess, args)
        pool.close()  # no more tasks
        pool.join()  # wrap up current tasks


    def unzip_multiprocess(self, file_name, save_path, zip_path):
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(save_path + "\\" + str(file_name))


    def generate_metrics(self, folder_path, languages="web"):
        output = subprocess.check_output("und create -languages " + str(languages) + " " + str(folder_path),
                                         shell=True)
        output2 = subprocess.check_output(
            "und add -db " + str(folder_path) + ".und " + str(folder_path),
            shell=True)
        output3 = subprocess.check_output("und analyze -db " + str(folder_path) + ".und",
                                          shell=True)
        with os.add_dll_directory("C:/Program Files/SciTools/bin/pc-win64"):
            import understand

            # print(understand.version())
            db = understand.open(str(folder_path) + ".und")
            metrics = db.metric(db.metrics())
            # for k, v in sorted(metrics.items()):
            #     print(k, "=", v)
            shutil.rmtree(str(folder_path) + ".und")
        version_name = os.path.basename(folder_path)
        metrics["version"] = version_name
        # import json

        # with open(str(version_name)+'.json', 'w') as fp:
            # json.dump(metrics, fp)
        # print(metrics)
        return metrics


    def generate_report_for_repository(self, folder_path, report_name="out.csv", languages="web"):
        folders = [join(folder_path, f) for f in os.listdir(folder_path) if os.path.isdir(join(folder_path, f))]
        metrics_list = defaultdict(list)
        for folder in folders:
            data = self.generate_metrics(folder_path=folder, languages=languages)
            for k, v in data.items():
                metrics_list[k].append(v)
        # print(metrics_list)
        df = pd.DataFrame.from_dict(metrics_list)
        df.to_csv(report_name, index=False)

        # data_df = pd.DataFrame.from_dict(metrics_list)
        return metrics_list



if __name__ == "__main__":

    #Download by Releases
    # GithubReleaseDownloader(access_token="948292454bf5f496035bc436b15d03c183cf0fe9").).download_releases(
    # repository="tiangolo/fastapi", save_path=r'E:\repo', thread_number=5)

    # Download by Tags
    # GithubReleaseDownloader(access_token="948292454bf5f496035bc436b15d03c183cf0fe9").download_tags(
    #     "elcodi/elcodi", thread_number=5, save_path="F:\Project_files")


    # Extract Zip
    # MetricsGenerator(source_folder=r"F:\Project_files\aimeos-core").unzip_all(
    # r"F:\Project_files\aimeos-core\extracted")

    # # Generate Report
    MetricsGenerator(source_folder=r"F:\Project_files\Sylius").generate_report_for_repository(
    r"F:\Project_files\Sylius\extracted", r"Sylius.csv")
