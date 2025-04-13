import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import json
import urllib.request

# 获取本机已安装的 Python 版本列表
# Get the list of installed Python versions on the local machine
def get_installed_python_versions():
    try:
        result = subprocess.run(['py', '-0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        lines = result.stdout.splitlines()
        versions = []
        for line in lines:
            line = line.strip()
            if line.startswith('-V:'):
                ver = line.split()[0][3:]
                versions.append(ver)
        return ['Default (Current System)'] + versions
    except Exception as e:
        messagebox.showerror('Error', f'Unable to get Python versions: {e}')
        return ['Default (Current System)']

# 检查 pip 是否可用
# Check if pip is available
def check_pip():
    try:
        result = subprocess.run(['pip', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise Exception(result.stderr)
    except Exception as e:
        messagebox.showerror('Error', f'pip not detected, please check your environment!\n\n{e}')
        root.destroy()

# 安装库逻辑
# Logic to install libraries
def install_packages(lib_list, mirror, pyver):
    progress.start(10)
    urls = {
        'Tsinghua Mirror': 'https://pypi.tuna.tsinghua.edu.cn/simple/',
        'Aliyun Mirror': 'https://mirrors.aliyun.com/pypi/simple/',
        'USTC Mirror': 'https://pypi.mirrors.ustc.edu.cn/simple/',
        'Tencent Cloud Mirror': 'https://mirrors.cloud.tencent.com/pypi/simple/',
        'Huawei Cloud Mirror': 'https://repo.huaweicloud.com/repository/pypi/simple/',
    }
    prefix = ['py', f'-{pyver}', '-m'] if pyver != 'Default (Current System)' else []

    for mn in lib_list:
        cmd = prefix + ['pip', 'install', mn]
        if mirror in urls:
            cmd += ['-i', urls[mirror]]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                messagebox.showinfo('Success', f'{mn} installed successfully')
            else:
                messagebox.showerror('Failure', f'{mn} installation failed\n\n{result.stderr}')
        except Exception as e:
            messagebox.showerror('Exception', f'Error during installation: {e}')
    progress.stop()

def download():
    lib_list = en.get().strip().split()
    mirror = com.get()
    pyver = pyver_com.get()
    if not lib_list:
        messagebox.showwarning('Tip', 'Please enter library names (separated by spaces)')
        return
    threading.Thread(target=install_packages, args=(lib_list, mirror, pyver)).start()

def upgrade_pip():
    threading.Thread(target=do_upgrade_pip).start()

def do_upgrade_pip():
    progress.start(10)
    try:
        result = subprocess.run(['pip', 'install', '--upgrade', 'pip'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            messagebox.showinfo('Success', 'pip upgraded successfully')
        else:
            messagebox.showerror('Failure', result.stderr)
    except Exception as e:
        messagebox.showerror('Exception', f'{e}')
    progress.stop()

# 根据选择的 Python 版本列出其已安装库
# List installed libraries for the selected Python version
def refresh_library_list_by_version():
    lib_listbox.delete(0, tk.END)
    pyver = pyver_manage_com.get()
    prefix = ['py', f'-{pyver}', '-m'] if pyver != 'Default (Current System)' else []
    cmd = prefix + ['pip', 'list', '--format=json']
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        data = json.loads(result.stdout)
        for item in data:
            lib_listbox.insert(tk.END, f"{item['name']}=={item['version']}")
    except Exception as e:
        messagebox.showerror('Error', f'Unable to list library list:\n{e}')

def uninstall_lib():
    selection = lib_listbox.curselection()
    if not selection:
        messagebox.showwarning('Tip', 'Please select a library first')
        return
    lib = lib_listbox.get(selection[0]).split('==')[0]
    if messagebox.askyesno('Confirm Uninstall', f'Are you sure you want to uninstall {lib}?'):
        threading.Thread(target=do_uninstall, args=(lib,)).start()

def do_uninstall(lib):
    result = subprocess.run(['pip', 'uninstall', lib, '-y'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        messagebox.showinfo('Tip', f'{lib} has been uninstalled')
        refresh_library_list_by_version()
    else:
        messagebox.showerror('Uninstall Failed', result.stderr)

def check_latest_version():
    selection = lib_listbox.curselection()
    if not selection:
        messagebox.showwarning('Tip', 'Please select a library')
        return
    lib = lib_listbox.get(selection[0]).split('==')[0]
    try:
        url = f'https://pypi.org/pypi/{lib}/json'
        with urllib.request.urlopen(url, timeout=5) as response:
            raw_data = response.read()
            data = json.loads(raw_data.decode('utf-8'))
            latest = data['info']['version']
            messagebox.showinfo('Latest Version', f'The latest version of {lib} is: {latest}')
    except Exception as e:
        messagebox.showerror('Query Failed', f'Unable to query version for {lib}\n{e}')

def install_specific_version():
    lib = custom_entry.get().strip()
    if lib == '':
        messagebox.showwarning('Tip', 'Please enter in the format: requests==2.31.0')
        return
    threading.Thread(target=do_install_specific, args=(lib,)).start()

def do_install_specific(lib):
    result = subprocess.run(['pip', 'install', lib], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        messagebox.showinfo('Success', f'{lib} installed successfully')
    else:
        messagebox.showerror('Failure', result.stderr)

def install_offline():
    path = filedialog.askopenfilename(filetypes=[('Wheel Files', '*.whl')])
    if path:
        threading.Thread(target=do_install_whl, args=(path,)).start()

def do_install_whl(path):
    result = subprocess.run(['pip', 'install', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        messagebox.showinfo('Success', f'Offline installation successful: {os.path.basename(path)}')
    else:
        messagebox.showerror('Failure', result.stderr)

def upgrade_all_libs():
    threading.Thread(target=do_upgrade_all_libs).start()

def do_upgrade_all_libs():
    progress.start(10)
    cmd = ['pip', 'list', '--format=json']
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        packages = json.loads(result.stdout)
        for item in packages:
            subprocess.run(['pip', 'install', '--upgrade', item['name']],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        messagebox.showinfo('Complete', 'Attempted to upgrade all libraries')
    except Exception as e:
        messagebox.showerror('Error', f'Error during upgrade: {e}')
    progress.stop()

# GUI
root = tk.Tk()
root.title('Python Install library tools Plus')
root.geometry('640x520')
root.configure(bg='#f0f4f7')
check_pip()

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both', padx=10, pady=10)

# Install page
install_frame = ttk.Frame(notebook)
notebook.add(install_frame, text='📦 Install Libraries')

ttk.Label(install_frame, text='Library Names (separated by spaces):').pack()
en = ttk.Entry(install_frame, width=55)
en.pack(pady=5)

ttk.Label(install_frame, text='Mirror Source:').pack()
com = ttk.Combobox(install_frame, width=53, state='readonly')
com['values'] = ('Default Source', 'Tsinghua Mirror', 'Aliyun Mirror', 'USTC Mirror', 'Tencent Cloud Mirror', 'Huawei Cloud Mirror')
com.pack(pady=5)

ttk.Label(install_frame, text='Python Version:').pack()
pyver_com = ttk.Combobox(install_frame, width=53, state='readonly')
pyver_com['values'] = get_installed_python_versions()
pyver_com.current(0)
pyver_com.pack(pady=5)

progress = ttk.Progressbar(install_frame, mode='indeterminate', length=450)
progress.pack(pady=10)

ttk.Button(install_frame, text='🚀 Install Libraries', command=download).pack(pady=5)
ttk.Button(install_frame, text='🔄 Upgrade pip', command=upgrade_pip).pack(pady=5)

ttk.Label(install_frame, text='Developer: Alan Mbe\n  time: Apr.13,2025').pack(side=tk.BOTTOM)

# Manage libraries page
manage_frame = ttk.Frame(notebook)
notebook.add(manage_frame, text='🧰 Manage Libraries')

ttk.Label(manage_frame, text='Select Python Version to View:').pack()
pyver_manage_com = ttk.Combobox(manage_frame, width=53, state='readonly')
pyver_manage_com['values'] = get_installed_python_versions()
pyver_manage_com.current(0)
pyver_manage_com.pack(pady=5)

ttk.Button(manage_frame, text='🔍 View Installed Libraries for Selected Python Version', command=refresh_library_list_by_version).pack(pady=5)

lib_listbox = tk.Listbox(manage_frame, width=85, height=15)
lib_listbox.pack(pady=5)

scroll = ttk.Scrollbar(manage_frame, command=lib_listbox.yview)
lib_listbox.config(yscrollcommand=scroll.set)
scroll.pack(side='right', fill='y')

btn_frame = ttk.Frame(manage_frame)
btn_frame.pack(pady=10)

ttk.Button(btn_frame, text='🔎 Check Latest Version', command=check_latest_version).grid(row=0, column=0, padx=10)
ttk.Button(btn_frame, text='❌ Uninstall Library (Current Version)', command=uninstall_lib).grid(row=0, column=1, padx=10)

# Advanced features page
advanced_frame = ttk.Frame(notebook)
notebook.add(advanced_frame, text='🧪 Advanced Features')

ttk.Label(advanced_frame, text='Install Specific Version (library==version):').pack(pady=5)
custom_entry = ttk.Entry(advanced_frame, width=50)
custom_entry.pack(pady=5)
ttk.Button(advanced_frame, text='📥 Install Specific Version', command=install_specific_version).pack(pady=5)

ttk.Button(advanced_frame, text='📦 Offline Install (Choose .whl file)', command=install_offline).pack(pady=10)
ttk.Button(advanced_frame, text='🆙 Upgrade All Libraries (Current Python)', command=upgrade_all_libs).pack(pady=5)

root.mainloop()
