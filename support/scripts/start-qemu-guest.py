#!/usr/bin/env python3
#
#    Copyright 2024 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Forked from support/scripts/boot-qemu-image.py.
#

import os
import shutil
import sys
import pexpect


def start_qemu(kernel_image: str, rootfs_image: str):
    if not os.path.exists(kernel_image):
        raise FileNotFoundError(f'{kernel_image} does not exist!')

    if not os.path.exists(rootfs_image):
        raise FileNotFoundError(f'{rootfs_image} does not exist!')

    qemu_path = shutil.which('qemu-system-x86_64')
    if qemu_path is None:
        raise FileNotFoundError('Cannot find qemu-system-x86_64 executable!')

    # TODO: Customize username, password, cores, threads, memory size, ...
    mem_size=512
    num_cores=2
    num_threads=2
    console='ttyS0'
    enable_kvm=True
    port=8022
    qemu_cmd = f'sudo {qemu_path} -kernel {kernel_image} -append "console={console}" ' \
               f'-smp cores={num_cores},threads={num_threads} -m {mem_size} ' \
               f'-netdev user,id=net0,hostfwd=tcp::{port}-:22 ' \
               f'-device virtio-net-pci,netdev=net0 --nographic ' \
               f'{"--enable-kvm" if enable_kvm else ""} -initrd {rootfs_image}'
    print(f'qemu_cmd: {qemu_cmd}')

    child = pexpect.spawn(qemu_cmd, timeout=10, encoding='utf-8')
    # XXX: Breaks interactive shell.
    #child.logfile = sys.stdout

    try:
        child.expect(['buildroot login:'], timeout=60)
    except pexpect.EOF:
        raise ConnectionError('Could not get login prompt!')
    except pexpect.TIMEOUT:
        raise TimeoutError('Target did not boot in time!')

    child.sendline('root\r')
    try:
        child.expect(['Password:'], timeout=10)
    except pexpect.EOF:
        raise ConnectionError('Cannot login to guest!')
    except pexpect.TIMEOUT:
        raise TimeoutError('Timeout while waiting for password prompt!')

    child.sendline('root\r')
    try:
        child.expect(['# '], timeout=10)
    except pexpect.EOF:
        raise ConnectionError('Login error!')
    except pexpect.TIMEOUT:
        raise TimeoutError('Timeout while waiting for shell prompt!')

    print('Guest is ready.')
    child.interact()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f'Wrong parameters! Sample usage: {sys.argv[0]} <kernel_image> <rootfs_image>')
        sys.exit(1)

    start_qemu(sys.argv[1], sys.argv[2])
