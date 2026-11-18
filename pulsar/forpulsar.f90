!$id:forpulsar.f90$
!
!author = Jean-Paul Amoureux <jean-paul.amoureux@univ-lille1.fr>
!contributors = C. Fernandez <christian.fernandez@ensicaen.fr>
!		J. Trebosc <julien.trebosc@univ-lille1.fr>
!
!PULSAR Project:
!
! Copyright (C) 2006-2007 Jean-Paul Amoureux, Christian Fernandez
! JPA - Unite de Catalyse et Chimie du Solide, Lille, France.
! CF  - Laboratoire Catalyse et Spectrochimie, Caen, France.
!
!LICENSE:
!
! This program is free software; you can redistribute it and/or
! modify it under the terms of the GNU General Public License (GPL)
! as published by the Free Software Foundation; either version 2
! of the License, or (at your option) any later version.
! This program is distributed in the hope that it will be useful,
! but WITHOUT ANY WARRANTY; without even the implied warranty of
! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
! GNU General Public License for more details.
! To read the license please visit http://www.gnu.org/copyleft/gpl.html
!
!PURPOSE OF THIS FILE:
!
!  Main file
!
!------------------------
include "diagonalize.f90" 
include "SUBROUTINEs.f90"
include "fourier.f90"
include "parameters.f90"
include "share.f90"
include "operators.f90"
include "ll.f90"
include "compute.f90"

program Main
! This main program will not be used 
! as a dll (pyd) will be created with f2y
end program
	
