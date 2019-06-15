import json
import os
from os import path

from langdetect import DetectorFactory, PROFILES_DIRECTORY
from langdetect.lang_detect_exception import LangDetectException, ErrorCode
from langdetect.utils.lang_profile import LangProfile


LANGUAGES_SHORTLIST = ['fr', 'en', 'de', 'it', 'es']


class FastDetectorFactory(DetectorFactory):

    def load_profile(self, profile_directory):
        list_files = os.listdir(profile_directory)
        if not list_files:
            raise LangDetectException(ErrorCode.NeedLoadProfileError, 'Not found profile: ' + profile_directory)

        lang_size, index = len(list_files), 0
        for filename in list_files:
            if filename not in LANGUAGES_SHORTLIST:
                continue
            filename = path.join(profile_directory, filename)
            if not path.isfile(filename):
                continue

            f = None
            try:
                f = open(filename, 'r', encoding='utf-8')
                json_data = json.load(f)
                profile = LangProfile(**json_data)
                self.add_profile(profile, index, lang_size)
                index += 1
            except IOError:
                raise LangDetectException(ErrorCode.FileLoadError, 'Cannot open "%s"' % filename)
            except:
                raise LangDetectException(ErrorCode.FormatError, 'Profile format error in "%s"' % filename)
            finally:
                if f:
                    f.close()


_factory = None


def init_factory():
    global _factory
    if _factory is None:
        _factory = FastDetectorFactory()
        _factory.load_profile(PROFILES_DIRECTORY)


def detect(text):
    init_factory()
    detector = _factory.create()
    detector.append(text)
    try:
        return detector.detect()
    except LangDetectException:
        return
