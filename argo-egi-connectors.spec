Name: argo-egi-connectors
Version: 1.4.4
Release: 3%{?dist}

Group: EGI/SA4
License: ASL 2.0
Summary: Components generate input for ARGO Compute Engine
Url: http://argoeu.github.io/guides/sync/
Vendor: SRCE <dvrcic@srce.hr, lgjenero@gmail.com>

Obsoletes: ar-sync
Prefix: %{_prefix}
Requires: avro
Requires: pyOpenSSL
Source0: %{name}-%{version}.tar.gz

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
Installs the components for syncing ARGO Compute Engine
with GOCDB, VO topology and POEM definitions per day.

%prep
%setup -n %{name}-%{version}

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install --directory %{buildroot}/%{_sharedstatedir}/argo-connectors/
install --directory %{buildroot}/%{_localstatedir}/log/argo-egi-connectors/
install --directory %{buildroot}/%{_libexecdir}/argo-egi-connectors/

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%attr(0755,root,root) %dir %{_libexecdir}/argo-egi-connectors/
%attr(0755,root,root) %{_libexecdir}/argo-egi-connectors/*.py*

%attr(0644,root,root) %{_sysconfdir}/cron.d/*

%attr(0750,root,root) %dir %{_sharedstatedir}/argo-connectors/
%attr(0750,root,root) %dir %{_localstatedir}/log/argo-egi-connectors/

%changelog
* Tue Oct 6 2015 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.4.4-3%{?dist}
- get scopes per customer (not globally)
* Tue Oct 6 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.4-2%{?dist}
- fix initialization of loggers in config parsers
- backward compatible exception messages
* Fri Oct 2 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.4-1%{?dist}
- filter SRM endpoints too
- refactored use of logging
- connectors can verify server certificate
  https://github.com/ARGOeu/ARGO/issues/153
- report correct number of fetched endpoints even if SRM endpoints were being filtered
- connectors handle help argument and describe basic info and usage
  https://github.com/ARGOeu/ARGO/issues/169
- removed hardcoded scopes and grab them dynamically from config
  https://github.com/ARGOeu/ARGO/issues/168
- report config parser errors via logger
- downtimes connector complain if wrong date specified
- remove notion of default scope
- doc moved to repo
- updated doc with server's cert validate options
* Wed Aug 19 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.3-3%{?dist}
- fix exception in case of returned HTTP 500 for other connectors
* Sat Aug 15 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.3-2%{?dist}
- fix poem-connector exception in case of returned HTTP 500
* Mon Aug 10 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.3-1%{?dist}
- generate meaningful statistic messages for every connector
- messages are written into syslog
  https://github.com/ARGOeu/ARGO/issues/116
* Wed Jul 15 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.2-2%{?dist}
- fixed bug with duplicating poem profiles info for prefilter
- fixed bug with SRM service type handling for topology and downtimes connectors
* Tue Jun 23 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.2-1%{?dist}
- changed internal parser structure to address entities with doubled scope
  https://github.com/ARGOeu/ARGO/issues/141
* Tue Jun 2 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.1-5%{?dist}
- new path and filename for consumer logs
* Thu May 28 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.1-4%{?dist}
- migrate.py lower on resources
* Thu May 21 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.1-3%{?dist}
- migration script to transform old data to new avro schema with map type
  https://github.com/ARGOeu/ARGO/issues/134
* Mon May 18 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.1-2%{?dist}
- GridPP VO job example
- downtimes filename day timestamp is queried one
  https://github.com/ARGOeu/ARGO/issues/133
* Wed May 6 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.1-1%{?dist}
- removed VO as an entity in configuration; only customers and set of jobs
- multiple customers in config each with own outputdir
- data feeds for all connectors can be defined per job
- prefilter-egi.py is aware of multiple customers
- avro schemas with generic tags
- case insensitive sections and options
- setup.py with automatic version catch from spec
- new default config
  https://github.com/ARGOeu/ARGO/issues/132
* Fri Apr 17 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-10%{?dist}
- VO jobs are moved under customer's directory
* Wed Apr 8 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-9%{?dist}
- handle group type names with whitespaces
- fixed bug with filtering VO groups across multiple VO jobs
* Fri Apr 3 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-8%{?dist}
- added Dirname optional option for VO config
- correctly renamed avro schemas
* Mon Mar 30 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-7%{?dist}
- added README.md with a basic project info  
* Sun Mar 29 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-6%{?dist}
- renamed weights and more configs refactoring
- put scripts back into libexec 
* Fri Mar 27 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-5%{?dist}
- minor code cleanups and renamed connectors to reflect the source of data
* Fri Mar 27 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-4%{?dist}
- poem server is defined in its config file, not global one
* Fri Mar 27 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-3%{?dist}
- prefilter-egi.py cleanups and roll back missing file
* Fri Mar 27 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-2%{?dist}
- deleted leftovers
* Fri Mar 27 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.4.0-1%{?dist}
- refactor the configuration of connectors/components
  https://github.com/ARGOeu/ARGO/issues/114
- fixed topology connector for VO'es to produce correct GE and GG avro files
  https://github.com/ARGOeu/ARGO/issues/121
- use of distutils for package building
* Tue Feb 17 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-16%{?dist}
- prefilter-avro has fixed configuration
* Thu Feb 12 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-15%{?dist}
- legacy SRM service type handle for downtime syncs
* Tue Feb 10 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-14%{?dist}
- updated .spec with removed configs for a per job prefilter-avro
* Tue Feb 10 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-13%{?dist}
- different internal handle of avro poem-sync so it doesn't contain duplicated entries
- special handle of legacy SRM service type
* Thu Feb 5 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-12%{?dist}
- plaintxt prefilter has fixed configuration
* Tue Feb 3 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-11%{?dist}
- update .spec to deploy new configs
- removed whitespaces at the end of config lines
* Mon Feb 2 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-10%{?dist}
- tools can have config file as their argument
- config files with changed output directory for customer/job
- modified cronjobs for customer and his two jobs
* Thu Jan 29 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-9%{?dist}
- bug fixes for poem-sync and prefilter
- typo in plaintext groups filename
* Mon Jan 19 2015 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-8%{?dist}
- topology-sync: avro schemas updated with tags and filtering by tags values
- poem-sync: avro schema updated with tags
- poem-sync: output profiles per customer and job
  https://github.com/ARGOeu/ARGO/issues/85
* Thu Jan 15 2015 Luko Gjenero <lgjenero@srce.hr> - 1.3.1-3%{?dist}
- avro prefiltering
* Wed Dec 17 2014 Daniel Vrcic <dvrcic@srce.hr> - 1.3.1-2%{?dist}
- ar-sync is missing avro dependency
- poem-sync is missing data for servers listed in URL
* Thu Nov 27 2014 Luko Gjenero <lgjenero@srce.hr> - 1.3.0-0%{?dist}
- Avro format for poem, downtimes, topology and hepspec
* Tue May 13 2014 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.2.3-1%{?dist}
- Added logging to sync components
* Fri Apr 26 2014 Luko Gjenero <lgjenero@srce.hr> - 1.2.2-1%{?dist}
- Updated prefilter
* Tue Mar 18 2014 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.2.1-1%{?dist}
- Updated daily cronjobs to run within first five minutes of each day
* Thu Jan 30 2014 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.1.19-1%{?dist}
- Updated daily cronjobs to run within first hour of each day
* Tue Jan 14 2014 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.1.18-1%{?dist}
- Added daily cronjob for hepspec values
* Thu Nov 28 2013 Luko Gjenero <lgjenero@srce.hr> - 1.1.16-3%{?dist}
- Fixed prefilter
* Thu Nov 28 2013 Luko Gjenero <lgjenero@srce.hr> - 1.1.16-2%{?dist}
- Fixed prefilter
* Thu Nov 28 2013 Luko Gjenero <lgjenero@srce.hr> - 1.1.16-1%{?dist}
- Updated prefilter
* Thu Nov 13 2013 Luko Gjenero <lgjenero@srce.hr> - 1.1.15-1%{?dist}
- VO Sync component
* Fri Nov 8 2013 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.1.0-1%{?dist}
- Inclusion of hepspec sync plus cronjobs
* Mon Nov 4 2013 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.0.0-6%{?dist}
- Fixes in consumer
* Tue Sep 17 2013 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.0.0-5%{?dist}
- Fix in prefilter
* Mon Sep 9 2013 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.0.0-4%{?dist}
- Rebuilt with fixed downtimes issue
* Thu Aug 29 2013 Paschalis Korosoglou <pkoro@grid.auth.gr> - 1.0.0-2%{?dist}
- Minor change in prefilter script
* Thu Aug 1 2013 Luko Gjenero <lgjenero@srce.hr> - 1.0.0-1%{?dist}
- Initial release

