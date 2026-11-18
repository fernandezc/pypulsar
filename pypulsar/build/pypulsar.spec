#Don't modify the following lines ******************************
__version__='0.2.alpha1.0-383'
__console__=True
#Don't modify the above lines ************************************

from os.path import normpath

#define DIRs
SRCDIR=normpath("P:/pyPulsar/trunk/pypulsar")
PYINSTALLER=normpath(SRCDIR+"/../pyinstaller")
BUILDDIR=normpath(SRCDIR+"/build")
DESTDIR=normpath(BUILDDIR+"/dist")
ADDTODIST=normpath(BUILDDIR+'/add_to_dist')
SVNDIR=normpath(SRCDIR+"/.svn")

imgpath=normpath((BUILDDIR+'/../images'))
print "imgpath",imgpath

print HOMEPATH

a = Analysis(
	[	normpath(PYINSTALLER+'/support/_mountzlib.py'),
		normpath(PYINSTALLER+'/support/useUnicode.py'),
		normpath(BUILDDIR+'/../pypulsar.py'),
	],
	pathex=[PYINSTALLER,BUILDDIR]
		)


pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts + [('v', '' ,'OPTION')],
          exclude_binaries=1,
          name=normpath('buildpypulsar/pypulsar.exe'),
          debug=False,
          strip=False,
          upx=False,
          console=__console__ , icon=normpath(imgpath+'/pypulsar.ico')
          )

##fichiers=[
##        ('images\\pypulsar-splash.bmp', imgpath+'pypulsar-splash.bmp', 'DATA'),
##        ('images\\pypulsar-installer.bmp', imgpath+'pypulsar-installer.bmp', 'DATA'),
##        ('images\\pypulsar-installer-small.bmp', imgpath+'pypulsar-installer-small.bmp', 'DATA'),
##		('images\\pypulsar.png', imgpath+'pypulsar.png', 'DATA'),
##		('forpulsar.pyd', installpath+'forpulsar.pyd','DATA'),
##		('pypulsar.cfg', installpath+'pypulsar.cfg','DATA'),
##        ('images\\pulfile.bmp',imgpath+'pulfile.bmp', 'DATA'),
##        ('images\\script.bmp',imgpath+'script.bmp', 'DATA'),
##        ('images\\log.png',imgpath+'log.png', 'DATA'),
##        ('images\\specfile.bmp',imgpath+'specfile.bmp', 'DATA'),
##        ('images\\expfile.bmp',imgpath+'expfile.bmp', 'DATA'),
##        ('images\\error.png',imgpath+'error.png', 'DATA'),
##        ('images\\noerror.png',imgpath+'noerror.png', 'DATA'),
##        ('README.html',installpath+'README.html', 'DATA'),
##        ('README.rtf',buildpath+'README.rtf', 'DATA'),
##        ('AUTHORS.rtf',buildpath+'AUTHORS.rtf', 'DATA'),
##        ('CHANGES.rtf',buildpath+'CHANGES.rtf', 'DATA'),
##        ('COPYING.rtf',buildpath+'COPYING.rtf', 'DATA'),
##        ('INSTALL.rtf',buildpath+'INSTALL.rtf', 'DATA'),
##        ('NEWS.rtf',buildpath+'NEWS.rtf', 'DATA'),
##        ('images\\pypulsar.ico',imgpath+'pypulsar.ico', 'DATA'),
##        ('images\\pypulsar-file.ico',imgpath+'pypulsar-file.ico', 'DATA'),
##        ('images\\pypulsar-installer.ico',imgpath+'pypulsar-installer.ico', 'DATA'),
##        ('images\\pypulsar-uninstaller.ico',imgpath+'pypulsar-uninstaller.ico', 'DATA'),
##        ('images\\pypulsar-logo.jpg',imgpath+'pypulsar-logo.jpg', 'DATA'),
##        ('images\\pypulsar-online.ico',imgpath+'pypulsar-online.ico', 'DATA'),
##        ]
fichiers =  [
            ('forpulsar.pyd', SRCDIR+'/forpulsar.pyd','DATA'),
            ]
coll = COLLECT( exe,
               a.binaries,
               fichiers,
               strip=False,
               upx=False,
               name='dist')
