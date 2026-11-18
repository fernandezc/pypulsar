#plot saved

#-------------------------------------------------------------------------------
    def plotSpectra_old(self):
#-------------------------------------------------------------------------------
        """
        PLOT_SPECTRA:
        Plot one or more 1D spectra on the same figure
        """
        cm.LOG_DEBUG("plot spectra")

        #Apply lb, gb and concentration.
        if self.do_processing and self.allow_processing:

            cm.LOG_DEBUG("Adding lb's and so on...")
            cm.LOG_DEBUG(self.n1, self.sw2, self.lb, self.gb,
                                                self.concentration)
            self.addLb(self.n1, self.spec, self.sw2, self.lb, self.gb,
                                                self.concentration)

        cm.LOG_DEBUG("Mode",self.__config['Mode'])
        cm.LOG_DEBUG("Kind",self.kind)

        #------------------------------------------------
        # We need to compute ppm, time or frequency scale
        #------------------------------------------------

        if self.kind in df.L_GRAPHS:
            cm.LOG_DEBUG("kind GRAPH")
            self.Mode = self.__config['Mode']="Intensity"
            cm.LOG_DEBUG("Mode set to ",self.Mode)

        if self.kind in df.L_SPECS:
            #Scaling in F2
            cm.LOG_DEBUG("kind in L_SPECS, calculate frequencies in F2:",
                                 self.n2, self.sw2,self.sr2, self.vl2)
            self.frequency2 = []
            self.ppm2 = []
            (a,b)=cm.P2F(self.n2, self.sw2, self.sr2)
            for point in range(self.n2):
                self.frequency2.append(a*point+b)
                self.ppm2.append( (a*point+b)*10.0**6/abs(self.vl2) )
                self.point2.append(point)

        if self.kind==df.EXP_2D:
            cm.LOG_DEBUG("kind EXPERIMENTAL 2D")
            (a,b)=cm.P2F(self.n1,self.sw1,self.sr1)
            self.frequency1=[]
            self.ppm1=[]
            for point in range(self.n1):
                self.frequency1.append(a*i+b)
                self.ppm1.append((a*i+b)/abs(self.vl1))
                self.point1.append(point)

        if self.kind in [df.EXP_FID,df.EXP_SER]:
            cm.LOG_DEBUG("kind EXPERIMENTAL FIDS")
            dw2=cm.F2T(self.sw2)
            self.time2=[]
            for point in range(self.n2):
                self.time2.append(dw2*point/1000.) #milliseconds
                self.point2.append(point)

        if self.kind==df.EXP_SER:
            cm.LOG_DEBUG("kind EXPERIMENTAL SER")
            dw1=cm.F2T(self.sw1)
            self.time1=[]
            for point in range(self.n1):
                self.time1.append(dw1*point/1000.)
                self.point1.append(point)

        #-------------
        # find maximum
        #-------------
        self.maxi=0
        for j in range(self.n1):
            mxi=max(map(abs,self.spec[j]))
            self.maxi=max(mxi,self.maxi)

        #Normalisation if we compare to experimental spectra
        #---------------------------------------------------
        self.norme=1.0
##        if self.spec_exp is not None:
##            self.maxi_exp=max(map(abs,self.spec_exp[0]))
##                   #by now only one experimental spectra (no series)
##            self.norme=self.maxi_exp/self.maxi
##            self.maxi=self.maxi_exp
##        else:
##            self.norme=1.0

        #To avoid an error when spectra are zero
        if self.maxi==0:
            self.spec=[]
            self.hasPlot = False
            return

##        #----------------------------------
##        # Prepare the subplot where to draw
##        #----------------------------------
##        LOG_DEBUG("Prepare Subplot")
##        self.fig.clear()
##        (w,h)=self.fig.get_size_inches()
##        dpi=self.fig.get_dpi()
##        self.fig.set_dpi(self.dpi)
##        self.fig.set_size_inches((w*dpi/self.dpi,h*dpi/self.dpi),forward=True)
##        self.plotdata = self.fig.add_subplot(111)
##
##        if not self.isAxe:
##            self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
##        else:
##            self.fig.subplots_adjust(left=0.1, bottom=0.1, right=.98, top=.90)

        #-------
        # Mode?
        #-------
        self.Mode=self.__config['Mode']
        if self.n1<3 and not (self.kind in df.L_GRAPHS):
            #The only acceptable Mode in this case (I think!)
            self.Mode=self.__config['Mode']="Standard"
        elif self.kind in df.L_GRAPHS:
            self.Mode=self.__config['Mode']="Intensities"

        cm.LOG_DEBUG("self.Mode",self.Mode)

        #-----------------------
        # Mode Standard 1D or 2D
        #-----------------------
        if self.Mode=="Standard" and self.kind in df.L_SPECS:

            cm.LOG_DEBUG("Start display in Mode",self.Mode)

            color=['g','c','m','y','k']
            ls=['--',':','-.','-']

            #Display Standard calculated files
            #---------------------------------
            if self.__config['Sum_Components'] or self.n1==1:
                self.__config['Sum_Components']=True
                self.__config['Y_Offset']=0.0

            self.__config['X_Offset']=0.0

            if string.lower(self.__config['X_Axis_Units'])=="hz":
                cm.LOG_DEBUG("Axis in Hz")
                self.X_scale=self.frequency2
                self.X_label='Frequency (Hz)'

            elif string.lower(self.__config['X_Axis_Units'])=="ppm":
                cm.LOG_DEBUG("Axis in ppm")
                self.X_scale=self.ppm2
                self.X_label='Chemical shift (ppm)'

            else:
                cm.LOG_DEBUG("Axis in points")
                self.X_Label='Points'
                self.X_scale=self.point2

            if self.__config['Show_Components']:
                cm.LOG_DEBUG("Show Components")
                if self.__config['Selected_Components']=="All":
                    comp=range(self.n1)
                else:
                    comp=[self.__config['Selected_Components']]
                for i in range(self.n1):
                    spec=[]
                    if str((i+1)) in comp:
                        cm.LOG_DEBUG("spec index",i)
                        # i+1 because index in selector start at 1!
                        shift=(i+1)*self.__config['Y_Offset']*self.maxi/100.
                        spec=[shift + x.real for x in self.spec[i]]
                        fmt=color[(i+6)%7]
                        if self.n1>1:
                                fmt+='-'
                        if self.__config['Sum_Components']:
                            fmt=color[i%6]+ls[i%3]
                        self.plotdata.plot(self.X_scale,
                                           array(spec)*self.norme,fmt)

            else:
                i=-1 #to avoid error with i in the next loop

##            if self.spec_exp is not None:
##                #show experiment
##                shift=(i+2)*self.__config['Y_Offset']*self.maxi_exp/100.
##                LOG_DEBUG("Y offset:", shift)
##                spec=[shift + x.real for x in array(self.spec_exp[0])]
##                #TODO: Il y a plus simple!!!!! use the numpy array techniques!!
##                self.plotdata.plot(self.X_scale,
##                                   array(spec),'r')

            #Add the sum spectra if necessary
            spec=[]
            cm.LOG_DEBUG("sum?",self.__config['Sum_Components'])
            if self.__config['Sum_Components']:
                #sum components
                self.spec_sum=array(self.sumSpectra(self.spec,self.n2,self.n1))
                shift=(i+2)*self.__config['Y_Offset']*self.maxi/100.
                cm.LOG_DEBUG("Y offset:", shift)
                spec=[shift + x.real for x in self.spec_sum]
                self.plotdata.plot(self.X_scale,
                                   array(spec)*self.norme,'b')

            self.plotdata.set_xlim(self.X_scale[len(self.X_scale)-1],
                                                         self.X_scale[0])
            self.plotdata.set_xlabel(self.X_label)
            self.Y_label='Intensity (a.u.)'

        #-------------------------
        # Mode Standard fid or ser
        #-------------------------
        if self.Mode=="Standard" and (self.kind=="fid" or self.kind=="ser"):
            #Fid or Ser (series of fid) display
            self.expoptions.OffsetY.Enable(False)
            self.expoptions.OffsetX.Enable(False)
            for i in range(self.n1):

                spec=[]
                self.SpecShowed=[0]
                # i+1 because index in selector start at 1!
                spec=[x.real for x in self.spec[i]]
                self.plotdata.plot(self.time2, array(spec))
                #if self.progress is not None:
            try:
                self.plotdata.set_xlim(self.time2[0],self.time2[len(self.time2)-1])
                self.plotdata.set_xlabel('time (ms)')
            except:
                self.plotdata.set_xlabel('points')

            self.ylabel='Intensity (a.u.)'



        #------------
        # TODO: Mode Series
        #------------
        if self.Mode == "Series":

            #set option state
            self.options.OffsetX.Enable(False)
            self.options.OffsetY.Enable(False)
            self.expoptions.OffsetX.Enable(False)
            self.expoptions.OffsetY.Enable(False)

            #init data for the ticks
            xticks=[]
            xtickslabel=[]
            spacing=10*(round(math.log10(self.n1))-1)
            #print spacing
            if spacing<2: spacing=4

            X=arange(0,self.n1,1.0/float(self.n2))
            Y=[]
            for i in range(self.n1):
                #iterate on the series of data
                Y=Y+[k.real for k in self.spec[i]]

                #Set the tick labels (if they were given)
                if self.ydata:
                    if i%spacing==0:
                        xticks.append(i+0.5)
                        xtickslabel.append(string.strip(str('%10.3f'%float(self.ydata[i]))))

                #update progress dialog
                #if self.progress is not None:

            self.plotdata.plot(X, array(Y))
            self.plotdata.set_xlim(0,self.n1)

            #if ydata exists, uses these xticklabels and the label
            if self.ydata:
                self.plotdata.set_xticks(xticks)
                self.plotdata.set_xticklabels(xtickslabel)
                self.plotdata.set_xlabel(self.label)
            else:
                self.plotdata.set_xlabel('Index')

            self.ylabel='Intensity (a.u.)'

        #-----------------
        # TODO: Mode Intensities
        #-----------------

        if self.Mode == "Intensities":
            self.options.OffsetX.Enable(False)
            self.options.OffsetY.Enable(False)
            self.expoptions.OffsetX.Enable(False)
            self.expoptions.OffsetY.Enable(False)

            xticks=[]
            xtickslabel=[]

            #print "graphe!"
            if not (self.kind in L_GRAPHS):

                spacing=10*(round(math.log10(self.n1))-1)
                if spacing<2: spacing=4
                X=range(self.n1)
                Y=[]
                for i in range(self.n1):
                    if self.ydata:
                        if i%spacing==0:
                            xticks.append(float(self.n2/2+i*self.n2)/self.n2)
                            xtickslabel.append(string.strip(str('%10.3f'%float(self.ydata[i]))))

                    Y.append(sum([k.real for k in self.spec[i]]))
                    #if self.progress is not None:

                self.plotdata.plot(X, array(Y),'bo--')
                self.plotdata.set_xlim(0,self.n1)

                self.plotdata.set_xlabel('Index')
                if self.ydata:
                    self.plotdata.set_xticks(xticks)
                    self.plotdata.set_xticklabels(xtickslabel)
                    self.plotdata.set_xlabel(self.label)

                self.ylabel='Intensity (a.u.)'

            else: #GRAPH 1D

                spacing=10*(round(math.log10(self.n2))-1)
                if spacing<2: spacing=4
                X=self.absc
                Z=self.spec
                Zexp=self.Zexp
                self.plotdata.plot(X, Z,'bo--')
                self.plotdata.plot(X, Zexp,'r^')

                self.plotdata.set_xlabel(self.xlabel)
                if self.ylabel=='':
                    self.ylabel='Intensity (a.u.)'

        #------------
        # TODO: Mode MAP 2D
        #------------

        if self.Mode == "Map" and self.kind!="ser":
            self.options.OffsetX.Enable(False)
            self.options.OffsetY.Enable(False)
            #if self.progress is not None:
            X=[]
            Y=[]
            Z=[]
            X=self.ppm2
            Y=range(self.n1)
            yticks=[]
            ytickslabel=[]
            spacing=10*(round(math.log10(self.n1))-1)
            if spacing<2: spacing=2
            maxi=0.
            mini=0.
            for i in range(self.n1):

                Zt=[k.real for k in self.spec[i]]
                mxi=max(Zt)
                mni=min(Zt)
                maxi=max(maxi,mxi)
                mini=min(mini,mni)
                Z.append(array(Zt))
                #if self.progress is not None:
                if self.ydata:
                    if i%spacing==0:
                        yticks.append(i)
##                        if not isinstance(self.ydata[i],str):
                        ytickslabel.append(string.strip(str('%10.3f'%float(self.ydata[i]))))
##                        else:
##                            ytickslabel.append(string.strip(str('%10.3f'%float(self.ydata[i]))))
            if mini<0:
                maxi=max(maxi,mini)
                mini=-maxi
                amp=2.*maxi
            else:
                amp=maxi

            levels=arange(mini-amp*.05,maxi+amp*.05,amp/self.n1)
            cmap=pylab.cm.get_cmap('jet', len(levels)-1)

            cset = self.plotdata.contourf(X, Y, Z, levels, cmap=cmap,)

            if self.contours:

                #TODO: Add an option to have contours
                self.plotdata.contour(X, Y, Z, cset.levels,     #cset2 =
                        colors = 'k',
                        hold='on')


            self.plotdata.set_xlim(self.ppm2[len(self.ppm2)-1],self.ppm2[0])
            self.plotdata.set_xlabel('Chemical shift (ppm)')
            self.ylabel='Index'
            if self.ydata:
                self.plotdata.set_yticks(yticks)
                self.plotdata.set_yticklabels(ytickslabel)
                self.ylabel=self.label

            #clabels=[mini,0.,maxi]
            #self.fig.colorbar(cset,clabels=clabels)

        #-------------
        # TODO: Mode MAP ser
        #-------------

        if self.Mode == "Map" and self.kind=="ser":
            self.options.OffsetX.Enable(False)
            self.options.OffsetY.Enable(False)
            self.expoptions.OffsetX.Enable(False)
            self.expoptions.OffsetY.Enable(False)
            #if self.progress is not None:
            X=[]
            Y=[]
            Z=[]
            X=self.time2
            Y=self.time1
            maxi=0.
            mini=0.
            for i in range(self.n1):
                Zt=[k.real for k in self.spec[i]]
                mxi=max(Zt)
                mni=min(Zt)
                maxi=max(maxi,mxi)
                mini=min(mini,mni)
                Z.append(array(Zt))
                #if self.progress is not None:

            if mini<0:
                maxi=max(maxi,mini)
                mini=-maxi
                amp=2.*maxi
            else:
                amp=maxi

            levels=arange(mini-amp*.05,maxi+amp*.05,amp/self.n1)
            cmap=pylab.cm.get_cmap('jet', len(levels)-1)

            cset = self.plotdata.contourf(X, Y, Z, levels, cmap=cmap,)

            if self.contours:
                self.plotdata.contour(X, Y, Z, cset.levels,
                        colors = 'k',
                        hold='on')

            self.plotdata.set_xlim(self.time2[0],self.time2[len(self.time2)-1])
            self.plotdata.set_xlabel('time (ms)')
            self.plotdata.set_xlim(self.time1[0],self.time1[len(self.time1)-1])
            self.ylabel='time (ms)'

        #----------------
        # TODO: Mode Stacked 2D
        #----------------

        if self.Mode=="Stacked" and self.kind!="ser":
            self.options.OffsetX.Enable(True)
            self.options.OffsetY.Enable(True)
            self.offsetX=self.options.OffsetX.GetValue()
            self.offsetY=self.options.OffsetY.GetValue()
            if string.lower(self.UnitX)=="hz":
                shiftx=abs(self.frequency2[len(self.frequency2)-1]-self.frequency2[0])*self.offsetX/100.
                for i in range(self.n1):

                    spec=[]
                    absc=[x-shiftx*(i-1) for x in self.frequency2]
                    if i==0:
                        llim=min(absc)
                    else:
                        llim=min(min(absc),llim)
                    if i==0:
                        hlim=max(absc)
                    else:
                        hlim=max(max(absc),hlim)
                    # i+1 because index in selector start at 1!
                    shift=(i+1)*self.offsetY*self.maxi/100.
                    spec=[shift + x.real for x in self.spec[i]]
                    self.plotdata.plot(absc, array(spec))
                    #if self.progress is not None:

                self.plotdata.set_xlim(hlim,llim)
                self.plotdata.set_xlabel('Frequency (Hz)')

            else:
                shiftx=abs(self.ppm2[len(self.ppm2)-1]-self.ppm2[0])*self.offsetX/100.
                for i in arange(self.n1-1,-1,-1):

                    spec=[]
                    absc=[x-shiftx*(i-1) for x in self.ppm2]
                    if i==self.n1-1:
                        llim=min(absc)
                    else:
                        llim=min(min(absc),llim)
                    if i==self.n1-1:
                        hlim=max(absc)
                    else:
                        hlim=max(max(absc),hlim)
                    shift=(i+1)*self.offsetY*self.maxi/100.
                    spec=[shift + x.real for x in self.spec[i]]
                    self.plotdata.plot(absc, array(spec))
                    self.plotdata.fill(absc, array(spec),facecolor='w',edgecolor='w')
                    #if self.progress is not None:

                self.plotdata.set_xlim(hlim,llim)
                self.plotdata.set_xlabel('Chemical shift (ppm)')

            self.ylabel='Intensity (a.u.)'

        #-----------------
        # TODO: Mode Stacked SER
        #-----------------
        if self.Mode=="Stacked" and self.kind=="ser":
            self.expoptions.OffsetX.Enable(True)
            self.expoptions.OffsetY.Enable(True)
            self.offsetX=self.expoptions.OffsetX.GetValue()
            self.offsetY=self.expoptions.OffsetY.GetValue()
            shiftx=-abs(self.time2[len(self.time2)-1]-self.time2[0])*self.offsetX/1000.
            for i in arange(self.n1-1,-1,-1):

                spec=[]
                absc=[x-shiftx*(i-1) for x in self.time2]
                if i==self.n1-1:
                    llim=min(absc)
                else:
                    llim=min(min(absc),llim)
                if i==self.n1-1:
                    hlim=max(absc)
                else:
                    hlim=max(max(absc),hlim)
                shift=(i+1)*self.offsetY*self.maxi/1000.
                spec=[shift + x.real for x in self.spec[i]]
                self.plotdata.plot(absc, array(spec))
                self.plotdata.fill(absc, array(spec),facecolor='w',edgecolor='w')
                ##if self.progress is not None:

            self.plotdata.set_xlim(llim,hlim)
            self.plotdata.set_xlabel('time (ms)')

            self.ylabel='Intensity (a.u.)'


        #-------
        # y axis
        #-------
        if self.__config['Show_Y_Axis']:
            self.plotdata.set_ylabel(self.Y_label)
        else:
            self.plotdata.set_yticks([])
            self.plotdata.set_yticklabels([])

        #----------------------
        # Title, grid and so on
        #----------------------
        if self.__config['Show_Title']:self.plotdata.set_title(self.__config['Title'])
        #print self.ShowGrid
        self.plotdata.grid(self.__config['Show_Grid'])

        #update everything and exit
        try:
            self.canvas.draw()
            ##self.toolbar.update()
        except:
            try:
                self.canvas.draw()
                ##self.toolbar.update()
            finally:
                pass

        #update the associated *.config

        #self.WritePlotCfgFile(self.fileoptions)

        #remove the progress dialog
        #if self.progress is not None: self.progress.Hide()

        self.timer.Stop()

        return True
