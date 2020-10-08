# GENERATED FILE, DO NOT EDIT.
# Run './gen-api-data.py > api_data.py' instead.
# fmt: off

API_URL = 'https://invalid-test-only.archive.softwareheritage.org/api/1'
ROOTREV_SWHID = 'swh:1:rev:d012a7190fc1fd72ed48911e77ca97ba4521bccd'
ROOTDIR_SWHID = 'swh:1:dir:9eb62ef7dd283f7385e7d31af6344d9feedd25de'
ROOTREV_URL = 'revision/d012a7190fc1fd72ed48911e77ca97ba4521bccd/'
ROOTREV_PARENT_URL = 'revision/cb95712138ec5e480db5160b41172bbc6f6494cc/'
ROOTDIR_URL = 'directory/9eb62ef7dd283f7385e7d31af6344d9feedd25de/'
README_URL = 'content/sha1_git:669ac7c32292798644b21dbb5a0dc657125f444d/'
README_RAW_URL = 'content/sha1_git:669ac7c32292798644b21dbb5a0dc657125f444d/raw/'

MOCK_ARCHIVE = {
    'revision/d012a7190fc1fd72ed48911e77ca97ba4521bccd/':  # NoQA: E501
    r"""{
  "author": {
    "email": "torvalds@linux-foundation.org",
    "fullname": "Linus Torvalds <torvalds@linux-foundation.org>",
    "name": "Linus Torvalds"
  },
  "committer": {
    "email": "torvalds@linux-foundation.org",
    "fullname": "Linus Torvalds <torvalds@linux-foundation.org>",
    "name": "Linus Torvalds"
  },
  "committer_date": "2020-08-23T14:08:43-07:00",
  "date": "2020-08-23T14:08:43-07:00",
  "directory": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
  "directory_url": "https://archive.softwareheritage.org/api/1/directory/9eb62ef7dd283f7385e7d31af6344d9feedd25de/",
  "extra_headers": [],
  "history_url": "https://archive.softwareheritage.org/api/1/revision/d012a7190fc1fd72ed48911e77ca97ba4521bccd/log/",
  "id": "d012a7190fc1fd72ed48911e77ca97ba4521bccd",
  "merge": false,
  "message": "Linux 5.9-rc2\n",
  "metadata": {},
  "parents": [
    {
      "id": "cb95712138ec5e480db5160b41172bbc6f6494cc",
      "url": "https://archive.softwareheritage.org/api/1/revision/cb95712138ec5e480db5160b41172bbc6f6494cc/"
    }
  ],
  "synthetic": false,
  "type": "git",
  "url": "https://archive.softwareheritage.org/api/1/revision/d012a7190fc1fd72ed48911e77ca97ba4521bccd/"
}
""",  # NoQA: E501
    'revision/cb95712138ec5e480db5160b41172bbc6f6494cc/':  # NoQA: E501
    r"""{
  "author": {
    "email": "torvalds@linux-foundation.org",
    "fullname": "Linus Torvalds <torvalds@linux-foundation.org>",
    "name": "Linus Torvalds"
  },
  "committer": {
    "email": "torvalds@linux-foundation.org",
    "fullname": "Linus Torvalds <torvalds@linux-foundation.org>",
    "name": "Linus Torvalds"
  },
  "committer_date": "2020-08-23T11:37:23-07:00",
  "date": "2020-08-23T11:37:23-07:00",
  "directory": "4fa3b43d90ce69b46916cc3fd3ea1d15de70443d",
  "directory_url": "https://archive.softwareheritage.org/api/1/directory/4fa3b43d90ce69b46916cc3fd3ea1d15de70443d/",
  "extra_headers": [
    [
      "mergetag",
      "object 64ef8f2c4791940d7f3945507b6a45c20d959260\ntype commit\ntag powerpc-5.9-3\ntagger Michael Ellerman <mpe@ellerman.id.au> 1598185676 +1000\n\npowerpc fixes for 5.9 #3\n\nAdd perf support for emitting extended registers for power10.\n\nA fix for CPU hotplug on pseries, where on large/loaded systems we may not wait\nlong enough for the CPU to be offlined, leading to crashes.\n\nAddition of a raw cputable entry for Power10, which is not required to boot, but\nis required to make our PMU setup work correctly in guests.\n\nThree fixes for the recent changes on 32-bit Book3S to move modules into their\nown segment for strict RWX.\n\nA fix for a recent change in our powernv PCI code that could lead to crashes.\n\nA change to our perf interrupt accounting to avoid soft lockups when using some\nevents, found by syzkaller.\n\nA change in the way we handle power loss events from the hypervisor on pseries.\nWe no longer immediately shut down if we're told we're running on a UPS.\n\nA few other minor fixes.\n\nThanks to:\n  Alexey Kardashevskiy, Andreas Schwab, Aneesh Kumar K.V, Anju T Sudhakar,\n  Athira Rajeev, Christophe Leroy, Frederic Barrat, Greg Kurz, Kajol Jain,\n  Madhavan Srinivasan, Michael Neuling, Michael Roth, Nageswara R Sastry, Oliver\n  O'Halloran, Thiago Jung Bauermann, Vaidyanathan Srinivasan, Vasant Hegde.\n-----BEGIN PGP SIGNATURE-----\n\niQJHBAABCAAxFiEEJFGtCPCthwEv2Y/bUevqPMjhpYAFAl9CYMwTHG1wZUBlbGxl\ncm1hbi5pZC5hdQAKCRBR6+o8yOGlgC/wEACljEVnfHzUObmIgqn9Ru3JlfEI6Hlk\nts7kajCgS/I/bV6DoDMZ8rlZX87QFOwiBkNM1I+vGHSLAuzsmFAnbFPyxw/idxpQ\nXUoNy8OCvbbzCPzChYdiU0PxW2h2i+QxkmktlWSN1SAPudJUWvoPS2Y4+sC4zksk\nB4B6tbW2DT8TFO1kKeZsU9r2t+EH5KwlIOi+uxbH8d76lJINKkBNSnjzMytl7drM\nTZx/HWr8+s/WJo1787x6bv8gxs5tV9b4vIKt2YZNTY2kvYsEDE+fBR1XfCAneXMw\nASYnZV+/xCLIUpRF6DI4RAShLBT/Sfiy1yMTndZgfqAgquokFosszNx2zrk0IzCd\nAgqX93YGbGz/H72W3Y/B0W9+74XyO/u2D9zhNpkCRMpdcsM5MbvOQrQA5Ustu47E\nav5MOaF/nNCd8J+OC4Qjgt5VFb/s0h4FdtrwT80srOa2U6Of9cD/T6xAfOszSJ96\ncWdSb5qhn5wuD9pP32KjwdmWBiUw38/gnRGKpRlOVzyHL/GKZijyaBbWBlkoEmty\n0nbjWW/IVfsOb5Weuiybg541h/QOVuOkb2pOvPClITiH83MY/AciDJ+auo4M//hW\nhaKz9IgV/KctmzDE+v9d0BD8sGmW03YUcQAPdRufI0eGXijDLcnHeuk2B3Nu84Pq\n8mtev+VQ+T6cZA==\n=sdJ1\n-----END PGP SIGNATURE-----"
    ]
  ],
  "history_url": "https://archive.softwareheritage.org/api/1/revision/cb95712138ec5e480db5160b41172bbc6f6494cc/log/",
  "id": "cb95712138ec5e480db5160b41172bbc6f6494cc",
  "merge": true,
  "message": "Merge tag 'powerpc-5.9-3' of git://git.kernel.org/pub/scm/linux/kernel/git/powerpc/linux\n\nPull powerpc fixes from Michael Ellerman:\n\n - Add perf support for emitting extended registers for power10.\n\n - A fix for CPU hotplug on pseries, where on large/loaded systems we\n   may not wait long enough for the CPU to be offlined, leading to\n   crashes.\n\n - Addition of a raw cputable entry for Power10, which is not required\n   to boot, but is required to make our PMU setup work correctly in\n   guests.\n\n - Three fixes for the recent changes on 32-bit Book3S to move modules\n   into their own segment for strict RWX.\n\n - A fix for a recent change in our powernv PCI code that could lead to\n   crashes.\n\n - A change to our perf interrupt accounting to avoid soft lockups when\n   using some events, found by syzkaller.\n\n - A change in the way we handle power loss events from the hypervisor\n   on pseries. We no longer immediately shut down if we're told we're\n   running on a UPS.\n\n - A few other minor fixes.\n\nThanks to Alexey Kardashevskiy, Andreas Schwab, Aneesh Kumar K.V, Anju T\nSudhakar, Athira Rajeev, Christophe Leroy, Frederic Barrat, Greg Kurz,\nKajol Jain, Madhavan Srinivasan, Michael Neuling, Michael Roth,\nNageswara R Sastry, Oliver O'Halloran, Thiago Jung Bauermann,\nVaidyanathan Srinivasan, Vasant Hegde.\n\n* tag 'powerpc-5.9-3' of git://git.kernel.org/pub/scm/linux/kernel/git/powerpc/linux:\n  powerpc/perf/hv-24x7: Move cpumask file to top folder of hv-24x7 driver\n  powerpc/32s: Fix module loading failure when VMALLOC_END is over 0xf0000000\n  powerpc/pseries: Do not initiate shutdown when system is running on UPS\n  powerpc/perf: Fix soft lockups due to missed interrupt accounting\n  powerpc/powernv/pci: Fix possible crash when releasing DMA resources\n  powerpc/pseries/hotplug-cpu: wait indefinitely for vCPU death\n  powerpc/32s: Fix is_module_segment() when MODULES_VADDR is defined\n  powerpc/kasan: Fix KASAN_SHADOW_START on BOOK3S_32\n  powerpc/fixmap: Fix the size of the early debug area\n  powerpc/pkeys: Fix build error with PPC_MEM_KEYS disabled\n  powerpc/kernel: Cleanup machine check function declarations\n  powerpc: Add POWER10 raw mode cputable entry\n  powerpc/perf: Add extended regs support for power10 platform\n  powerpc/perf: Add support for outputting extended regs in perf intr_regs\n  powerpc: Fix P10 PVR revision in /proc/cpuinfo for SMT4 cores\n",
  "metadata": {},
  "parents": [
    {
      "id": "550c2129d93d5eb198835ac83c05ef672e8c491c",
      "url": "https://archive.softwareheritage.org/api/1/revision/550c2129d93d5eb198835ac83c05ef672e8c491c/"
    },
    {
      "id": "64ef8f2c4791940d7f3945507b6a45c20d959260",
      "url": "https://archive.softwareheritage.org/api/1/revision/64ef8f2c4791940d7f3945507b6a45c20d959260/"
    }
  ],
  "synthetic": false,
  "type": "git",
  "url": "https://archive.softwareheritage.org/api/1/revision/cb95712138ec5e480db5160b41172bbc6f6494cc/"
}
""",  # NoQA: E501
    'directory/9eb62ef7dd283f7385e7d31af6344d9feedd25de/':  # NoQA: E501
    r"""[
  {
    "checksums": {
      "sha1": "39a0a88cd8eae4504e1d33b0c0f88059044d761f",
      "sha1_git": "a0a96088c74f49a961a80bc0851a84214b0a9f83",
      "sha256": "7c0f4eaf45838f26ae951b490beb0d11034a30b21e5c39a54c4223f5c2018890"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 16166,
    "name": ".clang-format",
    "perms": 33188,
    "status": "visible",
    "target": "a0a96088c74f49a961a80bc0851a84214b0a9f83",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:a0a96088c74f49a961a80bc0851a84214b0a9f83/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "0e31de4130c64f23e9ee5fc761fdbd807dc94360",
      "sha1_git": "43967c6b20151ee126db08e24758e3c789bcb844",
      "sha256": "dbd64d3f532b962d4681d79077cc186340f5f439de7f99c709b01892332af866"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 59,
    "name": ".cocciconfig",
    "perms": 33188,
    "status": "visible",
    "target": "43967c6b20151ee126db08e24758e3c789bcb844",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:43967c6b20151ee126db08e24758e3c789bcb844/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "52b62d115dfae2ed19561db14e8d10ee22659e7f",
      "sha1_git": "a64d219137455f407a7b1f2c6b156c5575852e9e",
      "sha256": "4c9ba8e0ef521ce01474e98eddfc77afaec8a8e259939a139590c00505646527"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 71,
    "name": ".get_maintainer.ignore",
    "perms": 33188,
    "status": "visible",
    "target": "a64d219137455f407a7b1f2c6b156c5575852e9e",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:a64d219137455f407a7b1f2c6b156c5575852e9e/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "6cc5a38e6f6ca93e21c78cb9c54794a42c3031c3",
      "sha1_git": "4b32eaa9571e64e47b51c43537063f56b204d8b3",
      "sha256": "dc52a4e1ee3615c87691aca7f667c7e49f6900f36b5c20339ac497366ba9406c"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 62,
    "name": ".gitattributes",
    "perms": 33188,
    "status": "visible",
    "target": "4b32eaa9571e64e47b51c43537063f56b204d8b3",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:4b32eaa9571e64e47b51c43537063f56b204d8b3/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "1966a794db7d9518f321a8ecb0736c16de59bd91",
      "sha1_git": "162bd2b67bdf6a28be7a361b8418e4e31d542854",
      "sha256": "a9766c936a81df2ed3ea41f506ddaad88a78d9cf47e093df414b3b6f2e6d8e14"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 1852,
    "name": ".gitignore",
    "perms": 33188,
    "status": "visible",
    "target": "162bd2b67bdf6a28be7a361b8418e4e31d542854",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:162bd2b67bdf6a28be7a361b8418e4e31d542854/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "2bb15bd51c981842b6f710d2e057972e5f22cfcc",
      "sha1_git": "332c7833057f51da02805add9b60161ff31aee71",
      "sha256": "d7b69571529964b3c8444a73ac720bbb883cc70fc4b78a36d1ac277f660c50bb"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 17283,
    "name": ".mailmap",
    "perms": 33188,
    "status": "visible",
    "target": "332c7833057f51da02805add9b60161ff31aee71",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:332c7833057f51da02805add9b60161ff31aee71/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "0473e748fee37c7b68487fb102c0d563bbc641b3",
      "sha1_git": "a635a38ef9405fdfcfe97f3a435393c1e9cae971",
      "sha256": "fb5a425bd3b3cd6071a3a9aff9909a859e7c1158d54d32e07658398cd67eb6a0"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 496,
    "name": "COPYING",
    "perms": 33188,
    "status": "visible",
    "target": "a635a38ef9405fdfcfe97f3a435393c1e9cae971",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:a635a38ef9405fdfcfe97f3a435393c1e9cae971/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "f27043aefa4b69b921df3728ee906c3f03087d29",
      "sha1_git": "32ee70a7562eec7345e98841473abb438379a4fd",
      "sha256": "23242c7183ee2815e27fea2346b0e5ad9131b8b611b200ae0418d4027cea2a3d"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 99788,
    "name": "CREDITS",
    "perms": 33188,
    "status": "visible",
    "target": "32ee70a7562eec7345e98841473abb438379a4fd",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:32ee70a7562eec7345e98841473abb438379a4fd/",
    "type": "file"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "Documentation",
    "perms": 16384,
    "target": "1ba46735273aa020a173c0ad0c813179530dd117",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/1ba46735273aa020a173c0ad0c813179530dd117/",
    "type": "dir"
  },
  {
    "checksums": {
      "sha1": "2491dd3bed10f6918ed1657ab5a7a8efbddadf5d",
      "sha1_git": "fa441b98c9f6eac1617acf1772ae8b371cfd42aa",
      "sha256": "75df66064f75e91e6458862cd9413b19e65b77eefcc8a95dcbd6bf36fd2e4b59"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 1327,
    "name": "Kbuild",
    "perms": 33188,
    "status": "visible",
    "target": "fa441b98c9f6eac1617acf1772ae8b371cfd42aa",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:fa441b98c9f6eac1617acf1772ae8b371cfd42aa/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "6b9b12a6bbff219dfbb45ec068af9aa7cf1b7288",
      "sha1_git": "745bc773f567067a85ce6574fb41ce80833247d9",
      "sha256": "a592dae7d067cd8e5dc43e3f9dc363eba9eb1f7cf80c6178b5cd291c0b76d3ec"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 555,
    "name": "Kconfig",
    "perms": 33188,
    "status": "visible",
    "target": "745bc773f567067a85ce6574fb41ce80833247d9",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:745bc773f567067a85ce6574fb41ce80833247d9/",
    "type": "file"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "LICENSES",
    "perms": 16384,
    "target": "a49a894ea3684b6c044448c37f812356550d14a2",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/a49a894ea3684b6c044448c37f812356550d14a2/",
    "type": "dir"
  },
  {
    "checksums": {
      "sha1": "eb207b62f2fe0225dc55d9b87d82f6009e864117",
      "sha1_git": "f0068bceeb6158a30c6eee430ca6d2a7e4c4013a",
      "sha256": "3c81b34eaf99d943e4c2fac2548f3d9d740a9e9683ccedbaacfb82796c7965e1"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 569101,
    "name": "MAINTAINERS",
    "perms": 33188,
    "status": "visible",
    "target": "f0068bceeb6158a30c6eee430ca6d2a7e4c4013a",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:f0068bceeb6158a30c6eee430ca6d2a7e4c4013a/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "9bfa205a4d23b9a60889bd9b59010574670b8b90",
      "sha1_git": "f2116815416091dbfa7dcf58ae179ae3241ec1b1",
      "sha256": "e87fb2b9482b9066b47c1656e55ebc4897bbb226daa122bcd4a2858fef19e597"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 63305,
    "name": "Makefile",
    "perms": 33188,
    "status": "visible",
    "target": "f2116815416091dbfa7dcf58ae179ae3241ec1b1",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:f2116815416091dbfa7dcf58ae179ae3241ec1b1/",
    "type": "file"
  },
  {
    "checksums": {
      "sha1": "ca1dc365022dcaa728dfb11bcde40ad3cce0574b",
      "sha1_git": "669ac7c32292798644b21dbb5a0dc657125f444d",
      "sha256": "bad58d396f62102befaf23a8a2ab6b1693fdc8f318de3059b489781f28865612"
    },
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": 727,
    "name": "README",
    "perms": 33188,
    "status": "visible",
    "target": "669ac7c32292798644b21dbb5a0dc657125f444d",
    "target_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:669ac7c32292798644b21dbb5a0dc657125f444d/",
    "type": "file"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "arch",
    "perms": 16384,
    "target": "cf12c1ce4de958ab4ddcb008fe89118b82a3c7b7",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/cf12c1ce4de958ab4ddcb008fe89118b82a3c7b7/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "block",
    "perms": 16384,
    "target": "a77c89fa64b8ec37c9aa0fa98add54bfb6075257",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/a77c89fa64b8ec37c9aa0fa98add54bfb6075257/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "certs",
    "perms": 16384,
    "target": "527d8f94235029c6f571414df5f8ed2951a0ca5b",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/527d8f94235029c6f571414df5f8ed2951a0ca5b/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "crypto",
    "perms": 16384,
    "target": "1fb1357e2d22af4332091937ed960a47f78d0b5e",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/1fb1357e2d22af4332091937ed960a47f78d0b5e/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "drivers",
    "perms": 16384,
    "target": "3b5be1ee0216ec59c70e132681be4a5d79e7da9b",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/3b5be1ee0216ec59c70e132681be4a5d79e7da9b/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "fs",
    "perms": 16384,
    "target": "1dbf8d211613db72f5b83b0987023bd5acf866ee",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/1dbf8d211613db72f5b83b0987023bd5acf866ee/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "include",
    "perms": 16384,
    "target": "74991fd1a983c6b3f72c8815f7de81a3abddb255",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/74991fd1a983c6b3f72c8815f7de81a3abddb255/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "init",
    "perms": 16384,
    "target": "c944a589113271d878e27bbc31ae369edecaff90",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/c944a589113271d878e27bbc31ae369edecaff90/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "ipc",
    "perms": 16384,
    "target": "ff553b9398fea6b2e290ea4a95f7a94f1cf3c22c",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/ff553b9398fea6b2e290ea4a95f7a94f1cf3c22c/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "kernel",
    "perms": 16384,
    "target": "8c700fd3589e6d2befa4d9b2cc79471eac37da38",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/8c700fd3589e6d2befa4d9b2cc79471eac37da38/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "lib",
    "perms": 16384,
    "target": "0f2936da43bebe4f26b3be83e8fa392c4f9e82cf",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/0f2936da43bebe4f26b3be83e8fa392c4f9e82cf/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "mm",
    "perms": 16384,
    "target": "e15d954c1ed09e6fc29c184515834696d8e70e7c",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/e15d954c1ed09e6fc29c184515834696d8e70e7c/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "net",
    "perms": 16384,
    "target": "41e1603b37542d265eade0555e0db66668135575",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/41e1603b37542d265eade0555e0db66668135575/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "samples",
    "perms": 16384,
    "target": "9fa649fea3c8ab6b4926f0e7721a21a36b685153",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/9fa649fea3c8ab6b4926f0e7721a21a36b685153/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "scripts",
    "perms": 16384,
    "target": "e4e5b45d7c44d0bd2c6feb1a257fff7303d2c67e",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/e4e5b45d7c44d0bd2c6feb1a257fff7303d2c67e/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "security",
    "perms": 16384,
    "target": "a4a58d89fc506c3660610105a08de60614cdc980",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/a4a58d89fc506c3660610105a08de60614cdc980/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "sound",
    "perms": 16384,
    "target": "bf9e1568b8ce61157a322fddbaab1a0c76be15ef",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/bf9e1568b8ce61157a322fddbaab1a0c76be15ef/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "tools",
    "perms": 16384,
    "target": "83d6279411023bf7edf6bde6ce2e3748912f4936",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/83d6279411023bf7edf6bde6ce2e3748912f4936/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "usr",
    "perms": 16384,
    "target": "aae2ca939e0f7ac6b5e489e4c7835e1a15588cff",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/aae2ca939e0f7ac6b5e489e4c7835e1a15588cff/",
    "type": "dir"
  },
  {
    "dir_id": "9eb62ef7dd283f7385e7d31af6344d9feedd25de",
    "length": null,
    "name": "virt",
    "perms": 16384,
    "target": "d7f6f10a8509839e404d1cc5af51317ac8b26276",
    "target_url": "https://archive.softwareheritage.org/api/1/directory/d7f6f10a8509839e404d1cc5af51317ac8b26276/",
    "type": "dir"
  }
]
""",  # NoQA: E501
    'content/sha1_git:669ac7c32292798644b21dbb5a0dc657125f444d/':  # NoQA: E501
    r"""{
  "checksums": {
    "blake2s256": "746aaa0816ffc8cadf5e7f70b8bb93a47a76299ef263c743dbfef2644c6a0245",
    "sha1": "ca1dc365022dcaa728dfb11bcde40ad3cce0574b",
    "sha1_git": "669ac7c32292798644b21dbb5a0dc657125f444d",
    "sha256": "bad58d396f62102befaf23a8a2ab6b1693fdc8f318de3059b489781f28865612"
  },
  "data_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:669ac7c32292798644b21dbb5a0dc657125f444d/raw/",
  "filetype_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:669ac7c32292798644b21dbb5a0dc657125f444d/filetype/",
  "language_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:669ac7c32292798644b21dbb5a0dc657125f444d/language/",
  "length": 727,
  "license_url": "https://archive.softwareheritage.org/api/1/content/sha1_git:669ac7c32292798644b21dbb5a0dc657125f444d/license/",
  "status": "visible"
}
""",  # NoQA: E501
    'content/sha1_git:669ac7c32292798644b21dbb5a0dc657125f444d/raw/':  # NoQA: E501
    r"""Linux kernel
============

There are several guides for kernel developers and users. These guides can
be rendered in a number of formats, like HTML and PDF. Please read
Documentation/admin-guide/README.rst first.

In order to build the documentation, use ``make htmldocs`` or
``make pdfdocs``.  The formatted documentation can also be read online at:

    https://www.kernel.org/doc/html/latest/

There are various text files in the Documentation/ subdirectory,
several of them using the Restructured Text markup notation.

Please read the Documentation/process/changes.rst file, as it contains the
requirements for building and running the kernel, and information about
the problems which may result by upgrading your kernel.
""",  # NoQA: E501
}
