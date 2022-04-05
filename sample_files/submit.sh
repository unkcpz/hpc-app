#!/bin/bash -l
#SBATCH --job-name="lammps-colloid"
#SBATCH --account="mrcloud"
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jusong.yu@epfl.ch
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-core=1
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=1
#SBATCH --partition=debug
#SBATCH --constraint=mc
#SBATCH --hint=nomultithread

module load daint-mc/20.08
module load LAMMPS/03Mar20-CrayGNU-20.08

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

'srun' '-n' '4' '/apps/daint/UES/jenkins/7.0.UP02/mc/easybuild/software/LAMMPS/03Mar20-CrayGNU-20.08/bin/lmp_mpi' '-in' 'colloid.in'