***Arizona Robotic Telescope Network Data Notification Agent***

The ARTN-DNA software is a series of bash and 1 Python script(s) to implement `.tgz` tarball creation and
distribution for users of the ARTN who have requested data via the *Observation Request Portal* (ARTN-ORP).

*This is not a web application although it runs under the www-data account!*

* REQUIREMENT(s)
   - bash
   - Python3.7

* SET UP:
    ```bash
     % cd /var/www/
     % git clone https://github.com/pndaly/ARTN-DNA.git
     % cd ARTN-DNA
     % mkdir logs
     % chown -R www-data:www-data /var/www/ARTN-DNA
    ```
 
* CRONTAB
    ```bash
     % crontab -l
     # +
     # subdue email output
     # -
     MAILTO=""
     # +
     # at 08:00, create yesterday's calibration tarballs
     # -
     0 8 * * * bash /var/www/ARTN-DNA/cron/TGZ.sh --iso=`date --date="yesterday" +\%Y\%m\%d` >> /var/www/ARTN-DNA/logs/DNA.log 2>&1
     # +
     # at noon, create tonight's observing files
     # -
     0 12 * * * bash /var/www/ARTN-DNA/cron/DNA.sh >> /var/www/ARTN-DNA/logs/DNA.log 2>&1
     # +
     # between 5 pm and midnight, run DNA.sh at 07,12,17,22,27,32,37,42,47,52,57 minutes past every hour
     # -
     7-59/5 17-23 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --gmail >> /var/www/ARTN-DNA/logs/DNA.log 2>&1
     # +
     # between midnight and 7 am, run DNA.sh at 07,12,17,22,27,32,37,42,47,52,57 minutes past every hour for the previous day
     # -
     7-59/5 0-7 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --iso=`date --date="yesterday" +\%Y\%m\%d` --gmail >> /var/www/ARTN-DNA/logs/DNA.log 2>&1
    ```

* RE-PROCESSING PREVIOUS DATA
    - Darks or skyflats (*Eg.* for 20190930)
    ```bash
     % source /var/www/ARTN-DNA/etc/DNA.sh
     % bash ${DNA_CRON}/TGZ.sh --iso=20190930 --over-ride --dry-run
     % bash ${DNA_CRON}/TGZ.sh --iso=20190930 --over-ride
    ```
    - Observation Data (*Eg.* for 20190930)
    ```bash
     % source /var/www/ARTN-DNA/etc/DNA.sh
     % bash ${DNA_BIN}/DNA.sh --iso=20190930 --over-ride --send-gmail --dry-run
     % bash ${DNA_BIN}/DNA.sh --iso=20190930 --over-ride --send-gmail
    ```

------------------------------------------------------------------------------------------------------------------------

Last Updated: 20191216
