"""Class to control openMVG behaviour."""

from pathlib import Path
import subprocess

import utils

logger = utils.create_logger("openmvg")

class OpenMVGControllerError(RuntimeError):
    """Generic openMVG error."""
    pass


class OpenMVGController():
    """Controls behaviour of openMVG data processing."""

    def __init__(self, res_dir):
        
        self.root_dir = Path(__file__).parent.parent.parent
        self.openMVG_dir = self.root_dir / "software" / "openMVG" / "build_openMVG"
        self.openMVG_dir = self.openMVG_dir / "Windows-AMD64-Release" / "Release"
        self.sensor_database = self.root_dir / "data" / "sensor_database" / "sensor_width_camera_database.txt"

        logger.info("openMVG executables dir %s", str(self.openMVG_dir))

        #self.input_dir = self.root_dir / "data" / "ImageDataset_SceauxCastle-master" / "images"
        self.input_dir = res_dir / "rendering"
        self.res_dir = res_dir

    def analyse_images(self,
                       focal=65437,
                       intrinsics=None,
                       cam_model=1,
                       prior=True,
                       p_weights=(1.0,1.0,1.0)):
        """ImageListing step of reconstruction."""
        logger.info("Start Imagelisting")

        self.matches_dir = self.res_dir / "matches"
        self.matches_dir = utils.check_dir(self.matches_dir)

        args = [str(self.openMVG_dir / "openMVG_main_SfMInit_ImageListing")]
        args.extend(["-i", str(self.input_dir)])
        args.extend(["-d", str(self.sensor_database)])
        args.extend(["-o", str(self.matches_dir)])

        args.extend(["-f", str(focal)])
        if intrinsics is not None:
            args.extend(["-k", intrinsics])
        args.extend(["-c", str(cam_model)])
        if prior:
            args.extend(["-P"])
            args.extend(["-W", ";".join([str(value) for value in p_weights])])

        ret = subprocess.run(args)
        logger.info("Image analysis returned: %s", str(ret))

    def compute_features(self,
                         force_compute=False,
                         descriptor="SIFT",
                         use_upright=True,
                         d_preset="ULTRA",
                         num_threads=0):
        """Compute features in images."""
        logger.info("Compute features of listed images")
 
        self.sfm_data = self.matches_dir / "sfm_data.json"

        args = [str(self.openMVG_dir / "openMVG_main_ComputeFeatures")]
        args.extend(["-i", str(self.sfm_data)])
        args.extend(["-o", str(self.matches_dir)])

        args.extend(["-f", str(int(force_compute))])
        args.extend(["-m", str(descriptor)])
        args.extend(["-u", str(int(use_upright))])
        args.extend(["-p", str(d_preset)])
        args.extend(["-n", str(num_threads)])

        ret = subprocess.run(args)
        logger.info("Feature computation returned: %s", str(ret))

    def match_features(self,
                       force_compute=False,
                       ratio=0.8,
                       geo_model="f",
                       num_overlaps=3,
                       pairlist_file=None,
                       method="FASTCASCADEHASHINGL2",
                       guided=False,
                       cache_size=None):
        """Match computed features of images."""
        logger.info("Match features of images")

        args = [str(self.openMVG_dir / "openMVG_main_ComputeMatches")]
        args.extend(["-i", str(self.sfm_data)])
        args.extend(["-o", str(self.matches_dir)])

        args.extend(["-f", str(int(force_compute))])
        args.extend(["-r", str(ratio)])
        args.extend(["-g", str(geo_model)])
        args.extend(["-v", str(num_overlaps)])
        if pairlist_file is not None:
            args.extend(["-l", str(pairlist_file)])
        args.extend(["-n", str(method)])
        args.extend(["-m", str(int(guided))])
        if cache_size is not None:
            args.extend(["-c", str(cache_size)])

        ret = subprocess.run(args)
        logger.info("Feature matching returned: %s", str(ret))

    def reconstruct_seq(self,
                        first_image=None,
                        second_image=None,
                        cam_model=3,
                        refine_options="ADJUST_ALL",
                        prior=False,
                        match_file=None):
        """Reconstruct 3D models sequentially."""
        #set manually the initial pair to avoid the prompt question
        logger.info("Do incremental/sequential reconstructions")

        self.reconstruction_dir = self.res_dir / "sequential"
        self.reconstruction_dir = utils.check_dir(self.reconstruction_dir)

        args = [str(self.openMVG_dir / "openMVG_main_IncrementalSfM")]
        args.extend(["-i", str(self.sfm_data)])
        args.extend(["-m", str(self.matches_dir)])
        args.extend(["-o", str(self.reconstruction_dir)])

        if first_image is not None:
            args.extend(["-a", str(first_image)])
        if second_image is not None:
            args.extend(["-a", str(second_image)])
        args.extend(["-c", str(cam_model)])
        args.extend(["-f", str(refine_options)])
        args.extend(["-P", str(int(prior))])
        if match_file is not None:
            args.extend(["-M", str(match_file)])
        
        ret = subprocess.run(args)
        logger.info("Incremental reconstruction returned: %s", str(ret))

    def export_MVS(self, num_threads=0):
        """Export 3D model to MVS format."""
        logger.info("Exporting MVG result to MVS format")

        input_file = self.reconstruction_dir / "sfm_data.bin"
        self.export_dir = utils.check_dir(self.res_dir / "export")
        self.export_scene = self.export_dir / "scene.mvs"
        self.undistorted_dir = utils.check_dir(self.export_dir / "undistorted")

        args = [str(self.openMVG_dir / "openMVG_main_openMVG2openMVS")]
        args.extend(["-i", str(input_file)])
        args.extend(["-o", str(self.export_scene)])
        args.extend(["-d", str(self.undistorted_dir)])

        args.extend(["-n", str(num_threads)])

        ret = subprocess.run(args)
        logger.info("Exporting to MVS returned: %s", str(ret))