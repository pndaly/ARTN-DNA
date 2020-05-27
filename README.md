# Arizona Robotic Telescope Network Data Notification Agent

The ARTN-DNA software is a series of bash and 1 Python script(s) to implement `.tgz` tarball creation and
distribution for users of the ARTN who have requested data via the *Observation Request Portal* (ARTN-ORP).

This is not a web application although it runs under the www-data account!

### REQUIREMENT(s)
   - bash
   - Python3.7

### SET UP:
    ```bash
     % cd /var/www/
     % git clone https://github.com/pndaly/ARTN-DNA.git
     % cd ARTN-DNA
     % mkdir logs
     % chown -R www-data:www-data /var/www/ARTN-DNA
    ```
    
### CRONTAB
    ```bash
     MAILTO=""
     # +
     # after 08:00, create yesterday's calibration tarballs
     # -
     1 8 * * * bash /var/www/ARTN-DNA/cron/TGZ.sh --tel=Bok    --ins=90Prime  --iso=`date --date="yesterday" +\%Y\%m\%d` >> /tmp/TGZ.cron.log 2>&1
     2 8 * * * bash /var/www/ARTN-DNA/cron/TGZ.sh --tel=Bok    --ins=BCSpec   --iso=`date --date="yesterday" +\%Y\%m\%d` >> /tmp/TGZ.cron.log 2>&1
     3 8 * * * bash /var/www/ARTN-DNA/cron/TGZ.sh --tel=Kuiper --ins=Mont4k   --iso=`date --date="yesterday" +\%Y\%m\%d` >> /tmp/TGZ.cron.log 2>&1
     4 8 * * * bash /var/www/ARTN-DNA/cron/TGZ.sh --tel=MMT    --ins=BinoSpec --iso=`date --date="yesterday" +\%Y\%m\%d` >> /tmp/TGZ.cron.log 2>&1
     5 8 * * * bash /var/www/ARTN-DNA/cron/TGZ.sh --tel=Vatt   --ins=Vatt4k   --iso=`date --date="yesterday" +\%Y\%m\%d` >> /tmp/TGZ.cron.log 2>&1
     # +
     # after 12:00 (noon), create tonight's observing files
     # -
     1 12 * * * bash /var/www/ARTN-DNA/cron/DNA.sh --tel=Bok    --ins=90Prime  >> /tmp/DNA.cron.log 2>&1
     2 12 * * * bash /var/www/ARTN-DNA/cron/DNA.sh --tel=Bok    --ins=BCSpec   >> /tmp/DNA.cron.log 2>&1
     3 12 * * * bash /var/www/ARTN-DNA/cron/DNA.sh --tel=Kuiper --ins=Mont4k   >> /tmp/DNA.cron.log 2>&1
     4 12 * * * bash /var/www/ARTN-DNA/cron/DNA.sh --tel=MMT    --ins=BinoSpec >> /tmp/DNA.cron.log 2>&1
     5 12 * * * bash /var/www/ARTN-DNA/cron/DNA.sh --tel=Vatt   --ins=Vatt4k   >> /tmp/DNA.cron.log 2>&1
     # +
     # between 16:00 and 00:00 (midnight), run DNA.sh at 5 minute intervals
     # -
     1-59/5 16-23 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=Bok    --ins=90Prime  --gmail >> /tmp/DNA.log 2>&1
     2-59/5 16-23 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=Bok    --ins=BCSpec   --gmail >> /tmp/DNA.log 2>&1
     3-59/5 16-23 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=Kuiper --ins=Mont4k   --gmail >> /tmp/DNA.log 2>&1
     4-59/5 16-23 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=MMT    --ins=BinoSpec --gmail >> /tmp/DNA.log 2>&1
     5-59/5 16-23 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=Vatt   --ins=Vatt4k   --gmail >> /tmp/DNA.log 2>&1
     # +
     # between 00:00 (midnight) and 08:00, run DNA.sh at 5 minute intervals
     # -
     1-59/5 0-8 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=Bok    --ins=90Prime  --iso=`date --date="yesterday" +\%Y\%m\%d` --gmail >> /tmp/DNA.log 2>&1
     2-59/5 0-8 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=Bok    --ins=BCSpec   --iso=`date --date="yesterday" +\%Y\%m\%d` --gmail >> /tmp/DNA.log 2>&1
     3-59/5 0-8 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=Kuiper --ins=Mont4k   --iso=`date --date="yesterday" +\%Y\%m\%d` --gmail >> /tmp/DNA.log 2>&1
     4-59/5 0-8 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=MMT    --ins=BinoSpec --iso=`date --date="yesterday" +\%Y\%m\%d` --gmail >> /tmp/DNA.log 2>&1
     5-59/5 0-8 * * * bash /var/www/ARTN-DNA/bin/DNA.sh --tel=Vatt   --ins=Vatt4k   --iso=`date --date="yesterday" +\%Y\%m\%d` --gmail >> /tmp/DNA.log 2>&1
    ```

### RE-PROCESSING PREVIOUS DATA
    - Calibration data (*Eg.* for 20191205)
    ```bash
     % source /var/www/ARTN-DNA/etc/DNA.sh
     % bash ${DNA_CRON}/TGZ.sh --tel=Bok    --ins=90Prime  --iso=20191205 --dry-run
     % bash ${DNA_CRON}/TGZ.sh --tel=Bok    --ins=BCSpec   --iso=20191205 --dry-run
     % bash ${DNA_CRON}/TGZ.sh --tel=Kuiper --ins=Mont4k   --iso=20191205 --dry-run
     % bash ${DNA_CRON}/TGZ.sh --tel=MMT    --ins=BinoSpec --iso=20191205 --dry-run
     % bash ${DNA_CRON}/TGZ.sh --tel=Vatt   --ins=Vatt4k   --iso=20191205 --dry-run
    ```
    - Observation Data (*Eg.* for 20191205)
    ```bash
     % source /var/www/ARTN-DNA/etc/DNA.sh
     % bash ${DNA_BIN}/DNA.sh --tel=Bok    --ins=90Prime  --iso=20191205 --over-ride --send-gmail --dry-run
     % bash ${DNA_BIN}/DNA.sh --tel=Bok    --ins=BCSpec   --iso=20191205 --over-ride --send-gmail --dry-run
     % bash ${DNA_BIN}/DNA.sh --tel=Kuiper --ins=Mont4k   --iso=20191205 --over-ride --send-gmail --dry-run
     % bash ${DNA_BIN}/DNA.sh --tel=MMT    --ins=BinoSpec --iso=20191205 --over-ride --send-gmail --dry-run
     % bash ${DNA_BIN}/DNA.sh --tel=Vatt   --ins=Vatt4k   --iso=20191205 --over-ride --send-gmail --dry-run
    ```
    - Specific Object (*Eg.* for 20191205 for object M51)
    ```bash
     % source /var/www/ARTN-DNA/etc/DNA.sh
     % python3.7 /var/www/ARTN-DNA/src/dna.py --data=/rts2data/Kuiper/Mont4k/20191205 --json=/rts2data/Kuiper/Mont4k/20191205/.dna.json --iso=20191205 --telescope=Kuiper --instrument=Mont4k --object=M51
    ```

    - Specific User (*Eg.* for 20191205 for user `another`)
    ```bash
     % source /var/www/ARTN-DNA/etc/DNA.sh
     % python3.7 /var/www/ARTN-DNA/src/dna.py --data=/rts2data/Kuiper/Mont4k/20191205 --json=/rts2data/Kuiper/Mont4k/20191205/.dna.json --iso=20191205 --telescope=Kuiper --instrument=Mont4k --user=another
    ```

    - Specific User and Object (*Eg.* for 20191205 for user `another`, object M51)
    ```bash
     % source /var/www/ARTN-DNA/etc/DNA.sh
     % python3.7 /var/www/ARTN-DNA/src/dna.py --data=/rts2data/Kuiper/Mont4k/20191205 --json=/rts2data/Kuiper/Mont4k/20191205/.dna.json --iso=20191205 --telescope=Kuiper --instrument=Mont4k --object=M51 --user=another
    ```

------------------------------------------------------------------------------------------------------------------------

Last Updated: 20200414
