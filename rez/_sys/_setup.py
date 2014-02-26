from __future__ import with_statement
from rez import module_root_path
from rez.system import system
import textwrap
import stat
import sys
import os
import os.path


try:
    assert(os.environ.get("__rez_is_installing"))
except:
    raise Exception("do not import _setup.py")


def _mkdirs(*dirs):
    path = os.path.join(*dirs)
    if not os.path.exists(path):
        os.makedirs(path)


def _mkpkg(name, version, content=None):
    dirs = [module_root_path, "packages", name, version]
    _mkdirs(*dirs)
    fpath = os.path.join(*(dirs + ["package.py"]))
    with open(fpath, 'w') as f:
        content = content or textwrap.dedent( \
        """
        config_version = 0
        name = '%(name)s'
        version = '%(version)s'
        """ % dict(name=name, version=version))
        f.write(content)


# create our own scripts, located inside the rez distribution, that will work within
# an unconfigured environment (ie, PYTHONPATH may not contain Rez).
def _create_scripts(install_base_dir, install_scripts_dir, version, scripts):
    new_bin_path = os.path.join(module_root_path, "bin")
    rel_install_base_dir = os.path.relpath(install_base_dir, new_bin_path)
    os.mkdir(new_bin_path)

    patch = textwrap.dedent( \
    """
    #!%(python_exe)s
    import sys
    import site
    import os.path
    _script_dir = os.path.dirname(__file__)
    _install_base = os.path.join(_script_dir, '%(rel_path)s')
    _install_base = os.path.realpath(_install_base)
    site.addsitedir(_install_base)
    sys.path.insert(0, _install_base)
    """ % dict(
        python_exe=sys.executable,
        rel_path=rel_install_base_dir))
    patch_loc = patch.split('\n')

    for script in scripts:
        file = os.path.join(install_scripts_dir, script)
        if os.path.isfile(file):
            mode = os.stat(file).st_mode
            with open(file) as f:
                code = f.read()

            loc = code.split('\n')
            shebang = loc[0]
            loc = patch_loc + loc[1:]

            # only patch python scripts, others are unchanged
            is_python = ("python" in shebang.lower())
            patched_code = '\n'.join(loc).strip() if is_python else code

            dst = os.path.join(new_bin_path, script)
            with open(dst, 'w') as f:
                f.write(patched_code)
            os.chmod(dst, mode)

    return new_bin_path


def post_install(install_base_dir, install_scripts_dir, version, scripts):
    # create patched scripts
    script_dir = _create_scripts(install_base_dir, install_scripts_dir,
                                 version, scripts)

    # create bootstrap packages
    print "Creating bootstrap package: platform..."
    _mkpkg("platform", system.platform)

    print "Creating bootstrap package: arch..."
    _mkpkg("arch", system.arch)

    print "Creating bootstrap package: os..."
    _mkpkg("os", system.os)