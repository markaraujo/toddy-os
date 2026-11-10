from pathlib import Path
import os,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build/phase2'))
from native_scratch_staging import allocation,workspace_paths,BASE,TARGET

class NativeScratchBudget(unittest.TestCase):
    def test_empty_files_and_directories_still_require_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'dir').mkdir();(root/'dir/empty').touch()
            self.assertGreater(allocation(root),0)

    def test_padding_and_dangling_link_are_counted_without_following(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').write_bytes(b'x'*4097);(root/'link').symlink_to('/unavailable-target')
            self.assertGreater(allocation(root),4097)

    def test_fifo_cannot_enter_a_native_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);os.mkfifo(root/'fifo')
            with self.assertRaises(AssertionError):allocation(root)

    def test_workspace_receipt_cannot_redirect_a_privileged_mount(self):
        good={'source':str(BASE/'toddy-editor-workers/native-transactions-1/output'),'target':str(TARGET/'sources/native-package-output')}
        for key,path in [('source','/etc'),('target','/usr'),('target',str(TARGET/'usr'))]:
            bad=dict(good);bad[key]=path
            with self.subTest(key=key,path=path),self.assertRaises(AssertionError):workspace_paths(bad)

if __name__=='__main__':unittest.main()
